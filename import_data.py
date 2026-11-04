import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

TABLES = [
    ("pharmacy", "pharmacy.csv"),
    ("pharma", "pharma.csv"),
    ("ingredient", "ingredient.csv"),
    ("illness", "illness.csv"),
    ("med", "med.csv"),
    ("med_ingredient", "med_ingredient.csv"),
    ("med_illness", "med_illness.csv"),
    ("dosage", "dosage.csv"),
    ("stock", "stock.csv"),
    ("import_batch", "import_batch.csv"),
]


def main():
    conninfo = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "pharmvault"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    with psycopg.connect(**conninfo) as conn:
        with conn.cursor() as cur:
            for table, filename in TABLES:
                path = ROOT / "datasets_local_stock" / filename

                with path.open("r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.reader(f)
                    columns = next(reader)

                    with cur.copy(
                        f"COPY {table} ({', '.join(columns)}) FROM STDIN"
                    ) as copy:
                        for row in reader:
                            copy.write_row(row)

                print(f"Imported {table}")

        conn.commit()

    print("Import complete.")


if __name__ == "__main__":
    main()
