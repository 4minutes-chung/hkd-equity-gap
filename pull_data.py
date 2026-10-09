"""Pull daily HKMA and FRED series for 2015 to today and merge them into one panel.

HKMA Monthly Statistical Bulletin XLS files on www.hkma.gov.hk (the HKMA Open API is blocked from this network):
  T060103  USD/HKD, Hang Seng Bank average closing middle rate
  T060303  1M HIBOR fixing, HONIA
  T070102  Aggregate Balance, closing
FRED: SOFR, 4-week T-bill.

Each raw download is saved untouched to data/raw/<name>_<timestamp>.{xls,csv}.
The panel goes to data/clean/panel.parquet, one row per 1M HIBOR fixing date
(Hong Kong business days) until the HSI is added. No forward-filling.
The panel is written only if the structural checks pass; the done-when content checks are reported.

Run with conda base:  python pull_data.py
"""
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import xlrd

START = "2015-01-01"
ROOT = Path(__file__).resolve().parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
MSB = "https://www.hkma.gov.hk/media/eng/doc/market-data-and-statistics/monthly-statistical-bulletin"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"

HKMA_TABLES = ("T060103", "T060303", "T070102")
# panel column: (table, sheet, column index, header texts that must appear above the data in that column)
HKMA_SERIES = {
    "usdhkd": ("T060103", "T6.1.3(new basket, 01.2020=100)", 3, ("U.S.", "dollar")),
    "hibor_1m": ("T060303", "T6.3.3 (HIBOR Fixing)", 5, ("1-month",)),
    "honia": ("T060303", "T6.3.3 (HONIA)", 2, ("Overnight",)),
    "agg_balance_hkd_mn": ("T070102", "T7.1.2", 12, ("Closing balance",)),
}
USD_OLD_SHEET = "T6.1.3(old basket, 01.2010=100)"  # same USD column; covers the years before the new sheet starts
FRED_SERIES = {"SOFR": "sofr", "DTB4WK": "tbill_4wk"}
# The USD/HKD series is a bank closing middle rate and sits up to 0.0035 outside 7.75 to 7.85 on 280 days.
BAND_LO, BAND_HI, BAND_TOL = 7.75, 7.85, 0.005  # tolerance proposed 2026-10-09, pending Steven


def download(url):
    """GET url; raise if the body is shorter than Content-Length (HKMA has returned truncated files with 200)."""
    r = requests.get(url, timeout=300, headers={"Accept-Encoding": "identity"})  # uncompressed, so lengths compare
    r.raise_for_status()
    expected = r.headers.get("Content-Length")
    if expected and int(expected) != len(r.content):
        raise RuntimeError(f"{url}: got {len(r.content)} bytes, expected {expected}")
    return r


def read_column(content, sheet, col, header):
    """One column of an HKMA bulletin sheet -> float series by date, from START on."""
    wb = xlrd.open_workbook(file_contents=content)
    sh = wb.sheet_by_name(sheet)
    dates, values, head = [], [], []
    for r in range(sh.nrows):
        d = sh.cell_value(r, 0)
        if isinstance(d, float) and d > 20000:  # data rows carry an Excel date serial in column 0
            dates.append(xlrd.xldate_as_datetime(d, wb.datemode))
            values.append(sh.cell_value(r, col))
        elif not dates:
            head.append(str(sh.cell_value(r, col)))
    missing = [h for h in header if not any(h in cell for cell in head)]
    if missing:
        raise RuntimeError(f"{sheet} column {col}: header {missing} not found, layout changed?")
    s = pd.Series(pd.to_numeric(pd.Series(values), errors="coerce").values,
                  index=pd.DatetimeIndex(dates)).sort_index(kind="stable")
    s = s[s.index >= START]
    if s.empty:
        raise RuntimeError(f"{sheet} column {col}: no data rows from {START}")
    return s


def pull(stamp):
    """Pull every series, saving raw files. Returns ({column: series}, {name: url}, {name: error})."""
    series, urls, failed, books = {}, {}, {}, {}
    for table in HKMA_TABLES:
        url = f"{MSB}/{table}.xls"
        try:
            books[table] = download(url).content
            urls[table] = url
            (RAW / f"{table}_{stamp}.xls").write_bytes(books[table])
        except Exception as e:  # report every failure at the end instead of stopping at the first
            failed[table] = f"{type(e).__name__}: {e}"
    for col, (table, sheet, c, header) in HKMA_SERIES.items():
        if table in books:
            try:
                series[col] = read_column(books[table], sheet, c, header).rename(col)
            except Exception as e:
                failed[col] = f"{type(e).__name__}: {e}"
    if "usdhkd" in series:
        try:  # prepend the old-basket sheet, after checking both sheets agree where they overlap
            new = series["usdhkd"]
            old = read_column(books["T060103"], USD_OLD_SHEET, 3, ("U.S.", "dollar"))
            overlap = old.index.intersection(new.index)
            if overlap.empty:
                raise RuntimeError("USD sheets do not overlap, cannot check they agree")
            pd.testing.assert_series_equal(old[overlap], new[overlap], check_names=False)
            series["usdhkd"] = pd.concat([old[old.index < new.index.min()], new]).rename("usdhkd")
        except Exception as e:
            failed["usdhkd_old_sheet"] = f"{type(e).__name__}: {e}"
    for fred_id, col in FRED_SERIES.items():
        name = f"fred_{fred_id.lower()}"
        try:
            r = download(f"{FRED}?id={fred_id}&cosd={START}")
            urls[name] = r.url
            (RAW / f"{name}_{stamp}.csv").write_bytes(r.content)
            df = pd.read_csv(StringIO(r.text))
            s = pd.Series(pd.to_numeric(df[fred_id], errors="coerce").values,
                          index=pd.to_datetime(df["observation_date"]), name=col).sort_index(kind="stable")
            series[col] = s[s.index >= START]
        except Exception as e:
            failed[name] = f"{type(e).__name__}: {e}"
    return series, urls, failed


def build_panel(series):
    """Left-join every series onto the 1M HIBOR fixing dates."""
    cal = series["hibor_1m"].index.unique().sort_values()  # every dated fixing row, even if the value is N.A.
    panel = pd.DataFrame(index=pd.DatetimeIndex(cal, name="date"))
    for col, s in series.items():
        panel[col] = s[~s.index.duplicated(keep="last")].reindex(panel.index)
    return panel


def structural_checks(panel, series):
    """Checks that block writing the panel. Returns list of (name, passed, detail)."""
    dups = {col: int(s.index.duplicated().sum()) for col, s in series.items()}
    dups["panel"] = int(panel.index.duplicated().sum())
    empty = [col for col in panel if panel[col].notna().sum() == 0]
    first = panel.index.min()
    return [
        ("no duplicate dates in panel or raw series", not any(dups.values()), str(dups)),
        ("no empty series in panel", not empty, f"empty: {empty}"),
        ("panel starts in the first week of 2015", first <= pd.Timestamp("2015-01-07"), f"first date {first}"),
    ]


def content_checks(panel):
    """The done-when data checks, reported but not blocking. Returns list of (name, passed, detail)."""
    def at(col, day):
        return panel[col].get(pd.Timestamp(day), float("nan"))

    fx = panel["usdhkd"].dropna()
    edge = fx[~fx.between(BAND_LO, BAND_HI)]
    out = fx[~fx.between(BAND_LO - BAND_TOL, BAND_HI + BAND_TOL)]
    ab_before, ab_after = at("agg_balance_hkd_mn", "2025-05-06"), at("agg_balance_hkd_mn", "2025-05-08")
    hibor_low = panel.loc["2025-05-01":"2025-07-31", "hibor_1m"].min()
    return [
        (f"USD/HKD within 7.75 to 7.85, tolerance {BAND_TOL}", len(fx) > 0 and out.empty,
         f"min {fx.min():.4f}, max {fx.max():.4f}, {len(edge)} days just past the band, "
         f"{len(out)} of {len(fx)} beyond tolerance; first: "
         + ", ".join(f"{d:%Y-%m-%d} {v:.4f}" for d, v in out.head(5).items())),
        ("Aggregate Balance ~45bn on 2025-05-06 and ~174bn on 2025-05-08",
         40_000 <= ab_before <= 50_000 and 170_000 <= ab_after <= 180_000,
         f"{ab_before:,.0f} mn -> {ab_after:,.0f} mn"),
        ("1M HIBOR below 1% in May to July 2025", hibor_low < 1.0, f"min {hibor_low:.3f}%"),
    ]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    CLEAN.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    series, urls, failed = pull(stamp)

    print("Sources used:")
    for name, url in urls.items():
        print(f"  {name}: {url}")
    print("Rows from 2015 on:")
    for col, s in series.items():
        print(f"  {col}: {s.notna().sum()} obs, {str(s.index.min())[:10]} to {str(s.index.max())[:10]}")
    if failed:
        print("FAILED pulls (panel not built):")
        for name, err in failed.items():
            print(f"  {name}: {err}")
        sys.exit(1)

    panel = build_panel(series)
    print(f"Panel: {len(panel)} rows, {panel.index.min():%Y-%m-%d} to {panel.index.max():%Y-%m-%d}")
    print(panel.notna().sum().to_string())
    structural, content = structural_checks(panel, series), content_checks(panel)
    for label, results in (("structural", structural), ("content", content)):
        for name, ok, detail in results:
            print(f"  {'PASS' if ok else 'FAIL'}  [{label}] {name}  ({detail})")
    if not all(ok for _, ok, _ in structural):
        print("Structural checks failed: data/clean/panel.parquet not written.")
        sys.exit(1)
    panel.to_parquet(CLEAN / "panel.parquet")
    print("Wrote data/clean/panel.parquet")


if __name__ == "__main__":
    main()
