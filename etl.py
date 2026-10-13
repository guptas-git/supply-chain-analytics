"""ELT pipeline: Olist CSVs + public-holiday API -> Postgres -> cleaned tables -> KPI marts -> checks -> CSVs for Tableau.

Run: python etl.py   (re-runnable; it rebuilds everything from data/ each time)
"""
import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

import psycopg

ROOT = Path(__file__).parent
DB = os.environ.get("DATABASE_URL", "dbname=supply_chain user=postgres")
HOLIDAY_API = "https://date.nager.at/api/v3/PublicHolidays/{year}/BR"
EXPORTS = ["order_facts", "seller_performance", "kpi_monthly", "exceptions"]


def table_name(csv_path):
    # olist_order_items_dataset.csv -> order_items
    return csv_path.stem.removeprefix("olist_").removesuffix("_dataset")


def load_raw(cur):
    """Extract + load: land every CSV as-is (all text) in schema raw. Typing happens in SQL."""
    cur.execute("DROP SCHEMA IF EXISTS raw CASCADE; CREATE SCHEMA raw")
    files = sorted((ROOT / "data").glob("*.csv"))
    if not files:
        sys.exit("No CSVs in data/. Download the Olist dataset first (see README).")
    for path in files:
        with open(path, encoding="utf-8-sig", newline="") as f:  # one file starts with a BOM
            header = next(csv.reader(f))
            cols = ", ".join(f'"{c}" text' for c in header)
            cur.execute(f"CREATE TABLE raw.{table_name(path)} ({cols})")
            with cur.copy(f"COPY raw.{table_name(path)} FROM STDIN WITH (FORMAT csv)") as copy:
                while chunk := f.read(1 << 20):
                    copy.write(chunk)
        print(f"  raw.{table_name(path):<35} {cur.execute(f'SELECT count(*) FROM raw.{table_name(path)}').fetchone()[0]:>9,} rows")


def load_holidays(cur):
    """Extract from the REST API: Brazilian national holidays (not state-only ones) for the years in the data."""
    cur.execute("CREATE TABLE raw.holidays (date text, name text)")
    years = cur.execute(
        "SELECT DISTINCT left(order_purchase_timestamp, 4)::int FROM raw.orders ORDER BY 1"
    ).fetchall()
    for (year,) in years:
        with urllib.request.urlopen(HOLIDAY_API.format(year=year), timeout=30) as r:
            holidays = json.load(r)
        cur.executemany("INSERT INTO raw.holidays VALUES (%s, %s)", [(h["date"], h["name"]) for h in holidays if h["global"]])
    print(f"  raw.holidays (API) {'':<22} {cur.execute('SELECT count(*) FROM raw.holidays').fetchone()[0]:>9,} rows")


def run_sql(cur, name):
    cur.execute((ROOT / "sql" / name).read_text())


def run_checks(cur):
    """Each check is a query that returns the rows breaking a rule. Any rows -> stop before exporting."""
    failed = []
    for check in (ROOT / "sql" / "checks.sql").read_text().split(";"):
        if not check.strip():
            continue
        name = [line for line in check.splitlines() if line.startswith("--")][-1].removeprefix("--").strip()
        bad = cur.execute(check).fetchall()
        print(f"  {'FAIL' if bad else 'ok  '}  {name}" + (f"  ({len(bad)} rows, e.g. {bad[0]})" if bad else ""))
        failed += [name] if bad else []
    if failed:
        sys.exit(f"{len(failed)} data-quality check(s) failed; exports not written.")


def export(cur):
    out = ROOT / "exports"
    out.mkdir(exist_ok=True)
    for view in EXPORTS:
        with open(out / f"{view}.csv", "wb") as f, cur.copy(f"COPY (SELECT * FROM mart.{view}) TO STDOUT WITH (FORMAT csv, HEADER)") as copy:
            for chunk in copy:
                f.write(chunk)
    n = cur.execute("SELECT count(*) FROM mart.exceptions").fetchone()[0]
    print(f"  wrote exports/*.csv; {n} exception(s) flagged -> exports/exceptions.csv")


def main():
    with psycopg.connect(DB) as conn, conn.cursor() as cur:  # one transaction: a failed run changes nothing
        print("Load")
        load_raw(cur)
        load_holidays(cur)
        print("Transform")
        run_sql(cur, "clean.sql")
        run_sql(cur, "marts.sql")
        print("Check")
        run_checks(cur)
        print("Export")
        export(cur)


if __name__ == "__main__":
    main()
