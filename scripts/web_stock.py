"""Build and load PharmVault's Web Stock from official US public-domain data.

Sources (both US government, public domain):
  * FDA NDC Directory      https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
                           (names, ingredients, strengths, dosage forms, manufacturers, Rx / OTC, drug class)
  * Medicaid NADAC prices  https://data.medicaid.gov  ("NADAC (National Average Drug Acquisition Cost) <year>")
                           (what US pharmacies pay per unit, in US dollars; only the newest week is used)

Usage (from the pharmvault folder):
  python scripts/web_stock.py build   # download newest data, write datasets_web_stock/web_medicines.csv
  python scripts/web_stock.py load    # load datasets_web_stock/web_medicines.csv into the database (in_web = TRUE)
  python scripts/web_stock.py all     # both

Raw downloads go to a temporary folder (or --raw DIR) and are never stored in the repository.
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "datasets_web_stock" / "web_medicines.csv"
FDA_ZIP_URL = "https://www.accessdata.fda.gov/cder/ndctext.zip"
MEDICAID_API = "https://data.medicaid.gov/api/1"
COLUMNS = ["med_name", "price", "type", "form", "pharma_name", "dosage_strength", "ingredients",
           "prescription_required", "ndc", "price_per_unit", "pricing_unit", "pack_units", "nadac_as_of"]

csv.field_size_limit(10**7)


# --------------------------------------------------------------------------- downloading

def fetch(url, dest):
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "pharmvault-web-stock-loader"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"  saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def api_json(path, params):
    url = f"{MEDICAID_API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "pharmvault-web-stock-loader"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def download_nadac(raw):
    """Download only the newest weekly NADAC snapshot (about 30k rows) instead of the whole year."""
    found = api_json("search", {"fulltext": "NADAC National Average Drug Acquisition Cost", "page-size": 50})
    items = found["results"].values() if isinstance(found["results"], dict) else found["results"]
    yearly = [i for i in items if re.fullmatch(r"NADAC \(National Average Drug Acquisition Cost\) \d{4}", i["title"])]
    newest = max(yearly, key=lambda i: i["title"])
    ds = newest["identifier"]
    top = api_json(f"datastore/query/{ds}/0", {"limit": 1, "count": "false", "schema": "false",
                                                 "sorts[0][property]": "as_of_date", "sorts[0][order]": "desc"})
    as_of = top["results"][0]["as_of_date"]
    print(f"  newest NADAC: {newest['title']}, week of {as_of}")
    dest = raw / f"nadac_{as_of}.csv"
    if not dest.exists():
        q = urllib.parse.urlencode({"format": "csv", "conditions[0][property]": "as_of_date",
                                    "conditions[0][value]": as_of, "conditions[0][operator]": "="})
        fetch(f"{MEDICAID_API}/datastore/query/{ds}/0/download?{q}", dest)
    return dest


def download_fda(raw):
    dest = raw / "ndctext.zip"
    if not dest.exists():
        fetch(FDA_ZIP_URL, dest)
    return dest


# --------------------------------------------------------------------------- cleaning helpers

def ndc11(code):
    """FDA 'labeler-product-package' (4-4-2, 5-3-2 or 5-4-1) -> 11-digit 5-4-2 code without dashes (NADAC style)."""
    a, b, c = code.split("-")
    return a.zfill(5) + b.zfill(4) + c.zfill(2)


def smart_title(text):
    text = " ".join(text.split())
    if not (text.isupper() or text.islower()):
        return text  # already mixed case, e.g. "Zepbound", "Eli Lilly and Company"
    out = []
    for w in text.split(" "):
        out.append(w if any(ch.isdigit() for ch in w) else w[:1].upper() + w[1:].lower())
    return " ".join(out)


FORM_RULES = [  # first match wins; maps FDA's 101 dosage forms onto PharmVault's 10 (+ other)
    ("drops", ("DROPS",)),
    ("injection", ("INJECT",)),
    ("syrup", ("SYRUP", "ELIXIR")),
    ("spray", ("SPRAY", "AEROSOL", "INHAL")),
    ("tablet", ("TABLET", "LOZENGE", "TROCHE")),
    ("capsule", ("CAPSULE",)),
    ("gel", ("GEL", "JELLY")),
    ("cream", ("CREAM", "OINTMENT", "LOTION", "PASTE")),
    ("powder", ("POWDER", "GRANULE")),
    ("liquid", ("SOLUTION", "SUSPENSION", "LIQUID", "CONCENTRATE", "EMULSION", "TINCTURE")),
]


def map_form(fda_form):
    f = fda_form.upper()
    for form, keys in FORM_RULES:
        if any(k in f for k in keys):
            return form
    return "other"


def pack_units(description):
    """'1 BOTTLE in 1 CARTON / 30 TABLET in 1 BOTTLE' -> 30 ; '10 BLISTER PACK in 1 CARTON / 10 TABLET ...' -> 100."""
    total = 1.0
    for seg in description.split("/"):
        m = re.match(r"\s*([\d.]+)\s", seg)
        if not m:
            return None
        try:
            total *= float(m.group(1))
        except ValueError:
            return None
    return total if 0 < total <= 100000 else None


def strength_text(nums, units):
    parts = []
    for n, u in zip(nums.split(";"), units.split(";")):
        n, u = n.strip(), u.strip()
        if not n:
            continue
        u = re.sub(r"/1$", "", u)  # "mg/1" -> "mg"
        parts.append(f"{n} {u}".strip())
    return " / ".join(parts)[:100]


def first_class(pharm_classes):
    m = re.search(r"([^,\[]+?) \[EPC\]", pharm_classes)
    return m.group(1).strip()[:100] if m else ""


# --------------------------------------------------------------------------- build

def build(raw):
    raw.mkdir(parents=True, exist_ok=True)
    print("1/3 downloading")
    nadac_path = download_nadac(raw)
    fda_zip = download_fda(raw)

    print("2/3 joining FDA products with NADAC prices")
    with zipfile.ZipFile(fda_zip) as z:
        product_txt = z.read("product.txt").decode("latin-1")
        package_txt = z.read("package.txt").decode("latin-1")
    products = {r["PRODUCTID"]: r for r in csv.DictReader(io.StringIO(product_txt), delimiter="\t")}
    packages = {}
    for r in csv.DictReader(io.StringIO(package_txt), delimiter="\t"):
        try:
            packages[ndc11(r["NDCPACKAGECODE"])] = r
        except ValueError:
            pass

    best = {}  # one row per drug per maker: same name + strength + form + labeler, cheapest pack wins
    matched = 0
    with nadac_path.open(encoding="utf-8-sig", newline="") as f:
        for n in csv.DictReader(f):
            pkg = packages.get(n["NDC"].zfill(11))
            p = products.get(pkg["PRODUCTID"]) if pkg else None
            if not p or p["PRODUCTTYPENAME"] not in ("HUMAN PRESCRIPTION DRUG", "HUMAN OTC DRUG"):
                continue
            matched += 1
            unit_price = float(n["NADAC Per Unit"])
            units = pack_units(pkg["PACKAGEDESCRIPTION"])
            price = max(round(unit_price * (units or 1), 2), 0.01)
            name = smart_title(" ".join(x for x in (p["PROPRIETARYNAME"], p["PROPRIETARYNAMESUFFIX"]) if x.strip()))[:250]
            form = map_form(p["DOSAGEFORMNAME"])
            strength = strength_text(p["ACTIVE_NUMERATOR_STRENGTH"], p["ACTIVE_INGRED_UNIT"])
            key = (name.lower(), strength.lower(), form, p["LABELERNAME"].strip().lower())
            row = {
                "med_name": name,
                "price": f"{price:.2f}",
                "type": first_class(p["PHARM_CLASSES"]),
                "form": form,
                "pharma_name": smart_title(p["LABELERNAME"])[:200],
                "dosage_strength": strength,
                "ingredients": "; ".join(smart_title(s.strip())[:200] for s in p["SUBSTANCENAME"].split(";") if s.strip()),
                "prescription_required": "true" if p["PRODUCTTYPENAME"] == "HUMAN PRESCRIPTION DRUG" else "false",
                "ndc": n["NDC"].zfill(11),
                "price_per_unit": n["NADAC Per Unit"],
                "pricing_unit": n["Pricing Unit"],
                "pack_units": f"{units:g}" if units else "",
                "nadac_as_of": n["As of Date"],
            }
            if key not in best or price < float(best[key]["price"]):
                best[key] = row

    rows = sorted(best.values(), key=lambda r: (r["med_name"].lower(), r["dosage_strength"], r["form"], r["pharma_name"].lower()))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"3/3 wrote {OUT_CSV.relative_to(ROOT)}: {len(rows)} medicines "
          f"(from {matched} priced packages, {OUT_CSV.stat().st_size / 1e6:.1f} MB)")


# --------------------------------------------------------------------------- load

def load():
    import psycopg
    from dotenv import load_dotenv
    from psycopg.rows import dict_row

    load_dotenv(ROOT / ".env")
    rows = list(csv.DictReader(OUT_CSV.open(encoding="utf-8", newline="")))
    print(f"loading {len(rows)} medicines from {OUT_CSV.relative_to(ROOT)}")
    conn_args = ({"conninfo": os.environ["DATABASE_URL"]} if os.getenv("DATABASE_URL") else
                 {"host": os.getenv("DB_HOST", "localhost"), "port": os.getenv("DB_PORT", "5432"),
                  "dbname": os.getenv("DB_NAME", "pharmvault"), "user": os.getenv("DB_USER", "postgres"),
                  "password": os.getenv("DB_PASSWORD", "")})
    with psycopg.connect(**conn_args, row_factory=dict_row) as conn:
        cur = conn.cursor()

        def next_id(table, col):
            cur.execute(f"SELECT COALESCE(MAX({col}), 0) + 1 AS n FROM {table}")
            return cur.fetchone()["n"]

        cur.execute("SELECT pharma_id, LOWER(pharma_name) AS k FROM pharma")
        pharma = {r["k"]: r["pharma_id"] for r in cur.fetchall()}
        cur.execute("SELECT ingredient_id, LOWER(ingredient_name) AS k FROM ingredient")
        ingred = {r["k"]: r["ingredient_id"] for r in cur.fetchall()}
        cur.execute("SELECT m.med_id, LOWER(m.med_name) AS name, COALESCE(LOWER(m.dosage_strength), '') AS s, "
                    "COALESCE(m.form, '') AS f, COALESCE(LOWER(p.pharma_name), '') AS maker "
                    "FROM med m LEFT JOIN pharma p ON p.pharma_id = m.pharma_id WHERE m.in_web")
        existing = {(r["name"], r["s"], r["f"], r["maker"]): r["med_id"] for r in cur.fetchall()}

        new_pharma, new_ingred = [], []
        pid, iid = next_id("pharma", "pharma_id"), next_id("ingredient", "ingredient_id")
        for r in rows:
            k = r["pharma_name"].lower()
            if k and k not in pharma:
                pharma[k] = pid
                new_pharma.append((pid, r["pharma_name"]))
                pid += 1
            for ing in filter(None, (x.strip() for x in r["ingredients"].split(";"))):
                if ing.lower() not in ingred:
                    ingred[ing.lower()] = iid
                    new_ingred.append((iid, ing))
                    iid += 1
        cur.executemany("INSERT INTO pharma (pharma_id, pharma_name) VALUES (%s, %s)", new_pharma)
        cur.executemany("INSERT INTO ingredient (ingredient_id, ingredient_name) VALUES (%s, %s)", new_ingred)

        mid = next_id("med", "med_id")
        inserts, updates, links, seen = [], [], [], set()
        for r in rows:
            key = (r["med_name"].lower(), r["dosage_strength"].lower(), r["form"], r["pharma_name"].lower())
            values = (r["price"], r["type"] or None, r["form"], pharma.get(r["pharma_name"].lower()),
                      r["dosage_strength"] or None, r["prescription_required"] == "true")
            if key in existing:
                med = existing[key]
                updates.append((*values, med))
            else:
                med = mid
                mid += 1
                inserts.append((med, r["med_name"], *values))
            seen.add(med)
            for ing in filter(None, (x.strip() for x in r["ingredients"].split(";"))):
                links.append((med, ingred[ing.lower()]))

        cur.executemany(
            "INSERT INTO med (med_id, med_name, price, type, form, pharma_id, dosage_strength, prescription_required, "
            "quantity, in_web) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, TRUE)", inserts)
        cur.executemany(
            "UPDATE med SET price = %s, type = %s, form = %s, pharma_id = %s, dosage_strength = %s, "
            "prescription_required = %s WHERE med_id = %s", updates)
        if updates:
            cur.execute("DELETE FROM med_ingredient WHERE med_id = ANY(%s)", ([u[-1] for u in updates],))
        cur.executemany("INSERT INTO med_ingredient (med_id, ingredient_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        links)
        # medicines that dropped out of the national data leave Web Stock (local stocks keep them)
        cur.execute("UPDATE med SET in_web = FALSE WHERE in_web AND NOT (med_id = ANY(%s))", (list(seen),))
        removed = cur.rowcount
        # Web Stock numbering: new catalogue medicines continue after the highest web_id (first load: 1, 2, 3 ...)
        cur.execute("""WITH base AS (SELECT COALESCE(MAX(web_id), 0) AS b FROM med),
     todo AS (SELECT med_id, ROW_NUMBER() OVER (ORDER BY med_id) AS rn FROM med WHERE in_web AND web_id IS NULL)
UPDATE med m SET web_id = (SELECT b FROM base) + todo.rn FROM todo WHERE m.med_id = todo.med_id""")
        cur.execute(
            "INSERT INTO import_batch (import_batch_id, source_name, source_type, record_count, import_date, notes) "
            "VALUES ((SELECT COALESCE(MAX(import_batch_id), 0) + 1 FROM import_batch), %s, %s, %s, CURRENT_DATE, %s)",
            ("FDA NDC Directory + Medicaid NADAC", "web_stock", len(rows),
             f"nadac week {rows[0]['nadac_as_of'] if rows else '?'}; {len(inserts)} added, {len(updates)} updated, "
             f"{removed} removed"))
    print(f"done: {len(inserts)} added, {len(updates)} updated, {removed} removed from Web Stock; "
          f"{len(new_pharma)} new pharma, {len(new_ingred)} new ingredients")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["build", "load", "all"])
    ap.add_argument("--raw", type=Path, help="folder for raw downloads (default: a new temporary folder)")
    args = ap.parse_args()
    if args.step in ("build", "all"):
        build(args.raw or Path(tempfile.mkdtemp(prefix="pharmvault_web_")))
    if args.step in ("load", "all"):
        load()


if __name__ == "__main__":
    sys.exit(main())
