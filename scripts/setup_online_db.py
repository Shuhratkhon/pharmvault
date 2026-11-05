"""Fill an EMPTY online PostgreSQL database (e.g. Neon) for PharmVault — run once from your own PC.

What it does:
  1. creates all tables from schema.sql
  2. loads the demo Local Stock data from datasets_local_stock/ (medicines, pharma, ingredients, illnesses,
     dosages) — but NO pharmacies: visitors create their own, and each new pharmacy gets the demo stock
  3. loads Web Stock from datasets_web_stock/web_medicines.csv (18,186 US medicines)

Usage (from the pharmvault folder):
  python scripts/setup_online_db.py
The script asks for the database connection string (input is hidden), so it never appears on screen,
in your shell history, or in any file.
"""

import csv
import getpass
import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# loaded in this order because of foreign keys; pharmacy.csv and stock.csv are left out on purpose
TABLES = ["pharma", "ingredient", "illness", "med", "med_ingredient", "med_illness", "dosage", "import_batch"]


def main():
    url = os.getenv("ONLINE_DATABASE_URL") or getpass.getpass("Paste the online database connection string: ").strip()
    if not url.startswith(("postgres://", "postgresql://")):
        sys.exit("That doesn't look like a PostgreSQL connection string (it should start with postgresql://).")

    with psycopg.connect(url) as conn:
        cur = conn.cursor()
        cur.execute("SELECT current_database(), version()")
        name, version = cur.fetchone()
        print(f"Connected to database '{name}' ({version.split(',')[0]})")
        cur.execute("SELECT to_regclass('public.med') IS NOT NULL")
        if cur.fetchone()[0]:
            sys.exit("This database already has PharmVault tables. Stopping, so nothing is overwritten.")

        print("1/3 creating tables from schema.sql")
        cur.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))

        print("2/3 loading demo Local Stock data (no pharmacies)")
        for table in TABLES:
            path = ROOT / "datasets_local_stock" / f"{table}.csv"
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                columns = next(reader)
                with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
                    for row in reader:
                        copy.write_row([None if v == "" else v for v in row])
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"    {table}: {cur.fetchone()[0]} rows")
        conn.commit()

    print("3/3 loading Web Stock")
    os.environ["DATABASE_URL"] = url
    import web_stock  # noqa: E402 — reuses the same loader as locally

    web_stock.load()
    print("Done. The online database is ready.")


if __name__ == "__main__":
    main()
