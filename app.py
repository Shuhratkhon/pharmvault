"""PharmVault — Flask backend serving the website and a JSON API over the PostgreSQL database."""

import csv
import io
import os
import re
import secrets
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request, send_file, send_from_directory, session
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

app = Flask(__name__, static_folder=None)


def _secret_key():
    """Key that signs the sign-in cookie. Kept in .env so sessions survive restarts."""
    key = os.getenv("SECRET_KEY")
    if not key:
        key = secrets.token_hex(32)
        with (ROOT / ".env").open("a", encoding="utf-8") as f:
            f.write(f"\nSECRET_KEY={key}\n")
    return key


app.config.update(
    SECRET_KEY=_secret_key(),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),  # stay signed in for 30 days
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),  # HTTPS-only cookie when running on Render
)
MIN_PASSWORD = 8

FRONTEND = ROOT / "frontend"  # index.html, style.css, script.js
FRONTEND_FILES = {"index.html", "style.css", "script.js"}
PAGE_SIZE_MAX = 100


def db():
    # Online (Render + Neon): one DATABASE_URL. Locally: the DB_* settings from .env.
    if os.getenv("DATABASE_URL"):
        return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pharmvault"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        row_factory=dict_row,
    )


def to_json(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def show(value):
    return "—" if value is None else str(to_json(value))


def rows_json(rows):
    return [{k: to_json(v) for k, v in r.items()} for r in rows]


def next_id(cur, table, column):
    cur.execute(f"SELECT COALESCE(MAX({column}), 0) + 1 AS n FROM {table}")
    return cur.fetchone()["n"]


def log(cur, pharmacy_id, stock, action, summary):
    cur.execute(
        "INSERT INTO history (pharmacy_id, stock_type, action, summary) VALUES (%s, %s, %s, %s)",
        (pharmacy_id or None, "local" if stock == "local" else "web", action, summary[:2000]),
    )


def seed_local_stock(cur, pharmacy_id):
    """Give a pharmacy its own copy of datasets_local_stock/stock.csv the first time it enters (once only)."""
    cur.execute("SELECT 1 FROM history WHERE pharmacy_id = %s AND action = 'seed'", (pharmacy_id,))
    if cur.fetchone():
        return
    with (ROOT / "datasets_local_stock" / "stock.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("stock_type", "local") == "local"]
    cur.execute("SELECT med_id FROM med")
    known = {r["med_id"] for r in cur.fetchall()}
    cur.execute("SELECT COUNT(*) AS c FROM stock WHERE pharmacy_id = %s AND stock_type = 'local'", (pharmacy_id,))
    before = cur.fetchone()["c"]
    start = next_id(cur, "stock", "stock_id")
    cur.executemany(
        "INSERT INTO stock (stock_id, pharmacy_id, med_id, stock_type, quantity, expiry_date, unit_price) "
        "VALUES (%s, %s, %s, 'local', %s, %s, %s) ON CONFLICT (pharmacy_id, med_id, stock_type) DO NOTHING",
        [(start + i, pharmacy_id, int(r["med_id"]), int(r["quantity"] or 0), r["expiry_date"] or None,
          r["unit_price"] or None) for i, r in enumerate(rows) if int(r["med_id"]) in known],
    )
    cur.execute("SELECT COUNT(*) AS c FROM stock WHERE pharmacy_id = %s AND stock_type = 'local'", (pharmacy_id,))
    added = cur.fetchone()["c"] - before
    log(cur, pharmacy_id, "local", "seed",
        f"Starter data loaded from the CSV files: {added} medicines" if added
        else "Starter data from the CSV files was already in this stock")


def int_arg(name, default, lo=1, hi=None):
    try:
        v = int(request.args.get(name, default))
    except (TypeError, ValueError):
        v = default
    v = max(lo, v)
    return min(v, hi) if hi else v


# --------------------------------------------------------------------------- front-end

@app.route("/")
def home():
    return send_from_directory(FRONTEND, "index.html")


@app.route("/<path:name>")
def frontend(name):
    if name not in FRONTEND_FILES:
        abort(404)
    return send_from_directory(FRONTEND, name)


# --------------------------------------------------------------------------- pharmacy

@app.get("/api/pharmacies")
def pharmacies():
    """Pharmacy names for the sign-in suggestions (names only)."""
    with db() as conn:
        rows = conn.execute("SELECT pharmacy_name FROM pharmacy ORDER BY pharmacy_name").fetchall()
    return jsonify([r["pharmacy_name"] for r in rows])


def current_pid():
    """The signed-in pharmacy. The server never trusts a pharmacy_id sent by the browser."""
    return session.get("pid") or 0


OPEN_API = {"/api/pharmacies", "/api/pharmacy/check", "/api/login", "/api/logout", "/api/me", "/api/form-limits"}


@app.before_request
def require_sign_in():
    if request.path.startswith("/api/") and request.path not in OPEN_API and not current_pid():
        return jsonify(error="Please sign in first", signed_out=True), 401


def pharmacy_info(cur, pid):
    cur.execute("SELECT pharmacy_id, pharmacy_name FROM pharmacy WHERE pharmacy_id = %s", (pid,))
    row = cur.fetchone()
    cur.execute("SELECT COUNT(*) AS c FROM stock WHERE pharmacy_id = %s AND stock_type = 'local'", (pid,))
    row["local_count"] = cur.fetchone()["c"]
    return row


def sign_in(pid):
    session.clear()
    session.permanent = True
    session["pid"] = pid


@app.post("/api/pharmacy/check")
def check_pharmacy():
    """Tells the sign-in page which step to show: 'login', 'set' (no password yet) or 'create' (new name)."""
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify(error="Enter a pharmacy name"), 400
    with db() as conn:
        row = conn.execute("SELECT pharmacy_name, password_hash FROM pharmacy WHERE LOWER(pharmacy_name) = LOWER(%s)",
                           (name,)).fetchone()
    if not row:
        return jsonify(step="create", name=name)
    return jsonify(step="login" if row["password_hash"] else "set", name=row["pharmacy_name"])


@app.post("/api/login")
def login():
    data = request.json or {}
    name = (data.get("name") or "").strip()[:150]
    password = data.get("password") or ""
    if not name:
        return jsonify(error="Enter a pharmacy name"), 400
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pharmacy_id, password_hash FROM pharmacy WHERE LOWER(pharmacy_name) = LOWER(%s)", (name,))
        row = cur.fetchone()
        if row and row["password_hash"]:
            if not check_password_hash(row["password_hash"], password):
                return jsonify(error="Wrong password"), 401
            pid = row["pharmacy_id"]
        else:
            # new pharmacy, or an existing one without a password yet: the first visitor sets it
            if len(password) < MIN_PASSWORD:
                return jsonify(error=f"Password must be at least {MIN_PASSWORD} characters"), 400
            if password != data.get("confirm"):
                return jsonify(error="The two passwords don't match"), 400
            hashed = generate_password_hash(password)
            if row:
                pid = row["pharmacy_id"]
                cur.execute("UPDATE pharmacy SET password_hash = %s WHERE pharmacy_id = %s", (hashed, pid))
            else:
                pid = next_id(cur, "pharmacy", "pharmacy_id")
                cur.execute("INSERT INTO pharmacy (pharmacy_id, pharmacy_name, pharmacy_country, password_hash) "
                            "VALUES (%s, %s, %s, %s)", (pid, name, "Unknown", hashed))
        seed_local_stock(cur, pid)
        info = pharmacy_info(cur, pid)
    sign_in(pid)
    return jsonify(info)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(status="signed out")


@app.get("/api/me")
def me():
    pid = current_pid()
    if not pid:
        return jsonify(error="Not signed in", signed_out=True), 401
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pharmacy WHERE pharmacy_id = %s", (pid,))
        if not cur.fetchone():
            session.clear()
            return jsonify(error="Not signed in", signed_out=True), 401
        return jsonify(pharmacy_info(cur, pid))


@app.post("/api/password")
def change_password():
    data = request.json or {}
    new = data.get("new") or ""
    if len(new) < MIN_PASSWORD:
        return jsonify(error=f"New password must be at least {MIN_PASSWORD} characters"), 400
    if new != data.get("confirm"):
        return jsonify(error="The two new passwords don't match"), 400
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM pharmacy WHERE pharmacy_id = %s", (current_pid(),))
        row = cur.fetchone()
        if not row or not check_password_hash(row["password_hash"] or "", data.get("current") or ""):
            return jsonify(error="Current password is wrong"), 400
        cur.execute("UPDATE pharmacy SET password_hash = %s WHERE pharmacy_id = %s",
                    (generate_password_hash(new), current_pid()))
    return jsonify(status="changed")


# --------------------------------------------------------------------------- medicines

# Warning limits per medicine form.
#   qty_yellow / qty_red: warn when quantity is UNDER this number
#   exp_yellow / exp_red: warn when the expiry date is this many days away OR LESS
# Quantity 0 and already-expired medicines are always red.
FORM_LIMITS = {
    "tablet":    {"qty_yellow": 40, "qty_red": 15, "exp_yellow": 120, "exp_red": 60},
    "capsule":   {"qty_yellow": 40, "qty_red": 15, "exp_yellow": 120, "exp_red": 60},
    "powder":    {"qty_yellow": 25, "qty_red": 10, "exp_yellow": 120, "exp_red": 60},
    "liquid":    {"qty_yellow": 25, "qty_red": 10, "exp_yellow": 60,  "exp_red": 30},
    "syrup":     {"qty_yellow": 25, "qty_red": 10, "exp_yellow": 60,  "exp_red": 30},
    "injection": {"qty_yellow": 15, "qty_red": 8,  "exp_yellow": 60,  "exp_red": 30},
    "cream":     {"qty_yellow": 20, "qty_red": 10, "exp_yellow": 90,  "exp_red": 45},
    "gel":       {"qty_yellow": 20, "qty_red": 10, "exp_yellow": 90,  "exp_red": 45},
    "drops":     {"qty_yellow": 20, "qty_red": 10, "exp_yellow": 45,  "exp_red": 21},
    "spray":     {"qty_yellow": 20, "qty_red": 10, "exp_yellow": 45,  "exp_red": 21},
}
DEFAULT_LIMITS = {"qty_yellow": 25, "qty_red": 10, "exp_yellow": 60, "exp_red": 30}  # other / no form


def limit_sql(key):
    """SQL CASE that picks the limit for each row's form."""
    whens = " ".join(f"WHEN '{form}' THEN {lim[key]}" for form, lim in FORM_LIMITS.items())
    return f"(CASE LOWER(form) {whens} ELSE {DEFAULT_LIMITS[key]} END)"


STOCK_LEVELS = ["Out of stock", "Very low", "Low", "In stock", "Not tracked"]
EXPIRY_LEVELS = ["Expired", "Expiring very soon", "Expiring soon", "Valid", "No expiry date"]
STOCK_STATUS = (
    "CASE WHEN quantity IS NULL THEN 'Not tracked' WHEN quantity = 0 THEN 'Out of stock' "
    f"WHEN quantity < {limit_sql('qty_red')} THEN 'Very low' "
    f"WHEN quantity < {limit_sql('qty_yellow')} THEN 'Low' ELSE 'In stock' END"
)
EXPIRY_STATUS = (
    "CASE WHEN expiry_date IS NULL THEN 'No expiry date' "
    "WHEN expiry_date < CURRENT_DATE THEN 'Expired' "
    f"WHEN expiry_date <= CURRENT_DATE + {limit_sql('exp_red')} THEN 'Expiring very soon' "
    f"WHEN expiry_date <= CURRENT_DATE + {limit_sql('exp_yellow')} THEN 'Expiring soon' ELSE 'Valid' END"
)
# Groups that have a natural order (worst first) instead of A–Z.
LEVEL_ORDER = {"stock_status": STOCK_LEVELS, "expiry_status": EXPIRY_LEVELS}


def group_sort(show_by, col):
    levels = LEVEL_ORDER.get(show_by)
    if not levels:
        return col
    arr = ", ".join(f"'{v}'" for v in levels)
    return f"array_position(ARRAY[{arr}]::text[], {col}), {col}"


def _level_list(levels):
    return "ARRAY[" + ", ".join(f"'{v}'" for v in levels) + "]::text[]"


# Watchlist = medicines with a red or yellow quantity or expiry warning (see FORM_LIMITS).
WATCH_WHERE = (f"(({STOCK_STATUS}) <> 'In stock' "
               f"OR ({EXPIRY_STATUS}) IN ('Expired', 'Expiring very soon', 'Expiring soon'))")
# 1 = out of stock / expired, 2 = very low / expiring very soon, 3 = low / expiring soon
WATCH_URGENCY = (f"LEAST(array_position({_level_list(STOCK_LEVELS)}, {STOCK_STATUS}), "
                 f"array_position({_level_list(EXPIRY_LEVELS)}, {EXPIRY_STATUS}))")


@app.get("/api/dashboard")
def dashboard():
    """Numbers for the Dashboard popup, for the current stock (local = this pharmacy)."""
    stock = "local" if request.args.get("stock") == "local" else "web"
    params = {"pid": current_pid()}
    base = f"({med_base(stock, None, None, None)}) b"
    with db() as conn:
        totals = conn.execute(
            f"SELECT COUNT(*) AS medicines, COALESCE(SUM(quantity), 0) AS packs, "
            f"COALESCE(SUM(quantity * price), 0) AS value FROM {base}", params).fetchone()
        by_form = conn.execute(
            f"SELECT COALESCE(INITCAP(form), 'No form') AS name, COUNT(*) AS count, "
            f"COALESCE(SUM(quantity * price), 0) AS value FROM {base} GROUP BY 1 ORDER BY count DESC, name",
            params).fetchall()
        expiry = conn.execute(
            f"""SELECT to_char(m, 'YYYY-MM') AS month, COUNT(b.med_id) AS count
                FROM generate_series(date_trunc('month', CURRENT_DATE),
                                     date_trunc('month', CURRENT_DATE) + interval '11 months',
                                     interval '1 month') m
                LEFT JOIN {base} ON date_trunc('month', b.expiry_date) = m
                GROUP BY m ORDER BY m""", params).fetchall()
        expired = conn.execute(f"SELECT COUNT(*) AS c FROM {base} WHERE expiry_date < CURRENT_DATE",
                               params).fetchone()["c"]
        illness = conn.execute(
            f"SELECT illness_name AS name, COUNT(*) AS count FROM {base} WHERE illness_name IS NOT NULL "
            f"GROUP BY 1 ORDER BY count DESC, name LIMIT 10", params).fetchall()
        by_type = conn.execute(
            f"SELECT COALESCE(type, 'No type') AS name, COUNT(*) AS count FROM {base} "
            f"GROUP BY 1 ORDER BY count DESC, name LIMIT 12", params).fetchall()
        pharma = conn.execute(
            f"SELECT pharma_name AS name, COUNT(*) AS count FROM {base} WHERE pharma_name IS NOT NULL "
            f"GROUP BY 1 ORDER BY count DESC, name LIMIT 10", params).fetchall()
        avg_price = conn.execute(
            f"SELECT COALESCE(INITCAP(form), 'No form') AS name, ROUND(AVG(price), 2) AS value, COUNT(*) AS count "
            f"FROM {base} GROUP BY 1 ORDER BY count DESC, name", params).fetchall()
        rx = conn.execute(f"SELECT COUNT(*) FILTER (WHERE prescription_required) AS rx, "
                          f"COUNT(*) FILTER (WHERE NOT prescription_required) AS otc FROM {base}", params).fetchone()
    return jsonify(totals={k: to_json(v) for k, v in totals.items()}, by_form=rows_json(by_form),
                   expiry=rows_json(expiry), expired=expired, illness=rows_json(illness),
                   by_type=rows_json(by_type), pharma=rows_json(pharma), avg_price=rows_json(avg_price),
                   rx=rx, stock=stock)


WATCH_LEVEL = (f"CASE WHEN ({STOCK_STATUS}) IN ('Out of stock', 'Very low') "
               f"OR ({EXPIRY_STATUS}) IN ('Expired', 'Expiring very soon') THEN 'red' ELSE 'yellow' END")


@app.get("/api/watchlist")
def watchlist():
    """Local-stock medicines with a warning: red section first, then yellow, each by ID."""
    with db() as conn:
        rows = conn.execute(
            f"""SELECT med_id, med_name, form, quantity, expiry_date,
                       {STOCK_STATUS} AS stock_status, {EXPIRY_STATUS} AS expiry_status, {WATCH_LEVEL} AS level
                FROM ({med_base("local", None, None, None)}) b
                WHERE {WATCH_WHERE}
                ORDER BY CASE WHEN {WATCH_LEVEL} = 'red' THEN 0 ELSE 1 END, med_id""",
            {"pid": current_pid()},
        ).fetchall()
    for r in rows:
        nice = {"Low": "Low stock", "Very low": "Very low stock"}
        r["reasons"] = [nice.get(s, s) for s in (r.pop("stock_status"), r.pop("expiry_status"))
                        if s not in ("In stock", "Valid", "No expiry date")]
    return jsonify(rows=rows_json(rows))


@app.get("/api/form-limits")
def form_limits():
    return jsonify(forms=FORM_LIMITS, default=DEFAULT_LIMITS)

SHOW_BY = {
    "alphabet": "NULL::text",
    "illness": "illness_name",
    "type": "type",
    "form": "form",
    "pharma": "pharma_name",
    "country": "pharma_country",
    "ingredients": "ingredients",
    "stock_status": STOCK_STATUS,
    "expiry_status": EXPIRY_STATUS,
    "prescription": "CASE WHEN prescription_required THEN 'Prescription required' ELSE 'Over the counter' END",
}

MED_ORDER = {
    "id": "med_id",
    "alphabet": "med_name, med_id",
    "price": "price, med_name",
    "schedule": "times_per_day NULLS LAST, med_name",
}
DOSAGE_AGE = {}  # order-by-age options removed; kept so the age filter code stays simple

MED_SORT_COLS = {
    "id": "med_id", "name": "med_name", "price": "price", "quantity": "quantity",
    "illness": "illness_name", "type": "type", "form": "form", "pharma": "pharma_name",
    "country": "pharma_country", "ingredients": "ingredients", "dosage": "dosage_strength",
    "expiry": "expiry_date", "rx": "prescription_required",
}


def med_base(stock, pharmacy_id, show_by, age):
    """SQL for one row per medicine (or per medicine+ingredient when grouping by ingredient)."""
    if stock == "local":
        stock_join = (
            "JOIN stock s ON s.med_id = m.med_id AND s.stock_type = 'local' AND s.pharmacy_id = %(pid)s"
        )
        price, qty, exp = "COALESCE(s.unit_price, m.price)", "s.quantity", "COALESCE(s.expiry_date, m.expiry_date)"
    else:
        stock_join, price, qty, exp = "", "m.price", "NULL::int", "NULL::date"  # catalogue: no stock / expiry
    web_where = "WHERE m.in_web" if stock != "local" else ""

    dosage_filter = "AND d.age_group = %(age)s" if age else ""
    base = f"""
        SELECT m.med_id, m.web_id, m.med_name, {price} AS price, {qty} AS quantity,
               il.illness_name, m.type, m.form, p.pharma_name, p.pharma_country,
               ing.ingredients, m.dosage_strength, {exp} AS expiry_date, m.prescription_required,
               ds.times_per_day, ds.age_groups, ing.ingredient_list
        FROM med m
        {stock_join}
        LEFT JOIN illness il ON il.illness_id = m.illness_id
        LEFT JOIN pharma p ON p.pharma_id = m.pharma_id
        LEFT JOIN LATERAL (
            SELECT string_agg(i.ingredient_name, ', ' ORDER BY i.ingredient_name) AS ingredients,
                   array_agg(i.ingredient_name ORDER BY i.ingredient_name) AS ingredient_list
            FROM med_ingredient mi JOIN ingredient i ON i.ingredient_id = mi.ingredient_id
            WHERE mi.med_id = m.med_id) ing ON TRUE
        LEFT JOIN LATERAL (
            SELECT MIN(d.times_per_day) AS times_per_day,
                   string_agg(DISTINCT d.age_group, ',') AS age_groups
            FROM dosage d WHERE d.med_id = m.med_id {dosage_filter}) ds ON TRUE
        {web_where}
    """
    return base


def med_filters():
    """WHERE clause over the base rows + params, shared by list and group endpoints."""
    stock = request.args.get("stock", "web")
    show_by = request.args.get("show_by", "alphabet")
    show_by = show_by if show_by in SHOW_BY else "alphabet"
    order = request.args.get("order", "id")
    order = order if order in MED_ORDER else "id"
    age = DOSAGE_AGE.get(order)
    q = request.args.get("q", "").strip()
    group = request.args.get("group")

    params = {"pid": current_pid(), "age": age}
    where = []
    if age:
        where.append("times_per_day IS NOT NULL")
    if q:
        params["like"] = f"%{q}%"
        cond = ("med_name ILIKE %(like)s OR ingredients ILIKE %(like)s OR illness_name ILIKE %(like)s "
                "OR pharma_name ILIKE %(like)s OR type ILIKE %(like)s OR form ILIKE %(like)s")
        m = re.fullmatch(r"[mM]?0*(\d+)", q)
        if m:
            params["qid"] = int(m.group(1))
            cond += " OR web_id = %(qid)s" if stock != "local" else " OR med_id = %(qid)s"
        where.append(f"({cond})")
    grp_expr = SHOW_BY[show_by]
    if group is not None and group != "":
        params["group"] = group
        if show_by == "ingredients":
            where.append("%(group)s = ANY(ingredient_list)")
        else:
            where.append(f"COALESCE({grp_expr}, '—') = %(group)s")

    if request.args.get("watch") == "1":
        where.append(WATCH_WHERE)

    sql_base = med_base("local" if stock == "local" else "web", params["pid"], show_by, age)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    return sql_base, where_sql, params, grp_expr, order, show_by


@app.get("/api/meds")
def list_meds():
    sql_base, where_sql, params, grp_expr, order, show_by = med_filters()
    per_page = int_arg("per_page", 10, hi=PAGE_SIZE_MAX)
    page = int_arg("page", 1)
    params.update(limit=per_page, offset=(page - 1) * per_page)

    sort = request.args.get("sort")
    direction = "DESC" if request.args.get("dir") == "desc" else "ASC"
    order_sql = MED_ORDER[order]
    if order == "id" and request.args.get("stock") != "local":
        order_sql = "web_id NULLS LAST, med_id"
    if sort in MED_SORT_COLS:
        order_sql = f"{MED_SORT_COLS[sort]} {direction} NULLS LAST, med_name"

    # When searching, medicines whose NAME matches come first; ingredient / illness / pharma matches follow.
    rank_sql = ""
    if "like" in params:
        rank_sql = "CASE WHEN med_name ILIKE %(like)s THEN 0 ELSE 1 END, "
    if request.args.get("watch") == "1":
        rank_sql = f"{WATCH_URGENCY}, " + rank_sql  # most urgent first

    sql = f"""
        SELECT b.*, COALESCE({grp_expr}, '—') AS grp, COUNT(*) OVER () AS total
        FROM ({sql_base}) b {where_sql}
        ORDER BY {rank_sql}{group_sort(show_by, f"COALESCE({grp_expr}, '—')")}, {order_sql}
        LIMIT %(limit)s OFFSET %(offset)s
    """
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    total = rows[0]["total"] if rows else 0
    for r in rows:
        r.pop("total")
        r.pop("ingredient_list", None)
    return jsonify(rows=rows_json(rows), total=total, page=page, per_page=per_page)


@app.get("/api/meds/groups")
def med_groups():
    sql_base, where_sql, params, grp_expr, _, show_by = med_filters()
    if show_by == "alphabet":
        return jsonify([])
    name_expr = "unnest(ingredient_list)" if show_by == "ingredients" else f"COALESCE({grp_expr}, '—')"
    sql = f"""
        SELECT name, COUNT(*) AS count
        FROM (SELECT {name_expr} AS name FROM ({sql_base}) b {where_sql}) g
        GROUP BY 1 ORDER BY {group_sort(show_by, 'name')}
    """
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return jsonify(rows_json(rows))


@app.get("/api/lookups")
def lookups():
    """Distinct values for the Add-row forms (datalists)."""
    with db() as conn:
        out = {
            "pharma": [r["v"] for r in conn.execute("SELECT pharma_name v FROM pharma ORDER BY 1")],
            "illness": [r["v"] for r in conn.execute("SELECT illness_name v FROM illness ORDER BY 1")],
            "ingredient": [r["v"] for r in conn.execute("SELECT ingredient_name v FROM ingredient ORDER BY 1")],
            "type": [r["v"] for r in conn.execute("SELECT DISTINCT type v FROM med WHERE type IS NOT NULL ORDER BY 1")],
            "form": [r["v"] for r in conn.execute("SELECT DISTINCT form v FROM med WHERE form IS NOT NULL ORDER BY 1")],
            "country": [r["v"] for r in conn.execute(
                "SELECT DISTINCT pharma_country v FROM pharma WHERE pharma_country IS NOT NULL ORDER BY 1")],
        }
    return jsonify(out)


# --------------------------------------------------------------------------- mother tables

TABLES = {
    "pharma": {
        "pk": "pharma_id",
        "cols": "pharma_id, pharma_name, pharma_country, pharma_market_value, pharma_origin_year",
        "search": ["pharma_name", "pharma_country"],
        "orders": {"id": "pharma_id", "alphabet": "pharma_name", "country": "pharma_country, pharma_name",
                   "market_value": "pharma_market_value DESC NULLS LAST, pharma_name"},
        "sort": {"id": "pharma_id", "name": "pharma_name", "country": "pharma_country",
                 "market_value": "pharma_market_value", "created": "pharma_origin_year"},
        "web": "pharma_id IN (SELECT pharma_id FROM med WHERE in_web)",
        "local": "pharma_id IN (SELECT m.pharma_id FROM med m JOIN stock s ON s.med_id = m.med_id "
                 "WHERE s.stock_type = 'local' AND s.pharmacy_id = %(pid)s)",
    },
    "ingredient": {
        "pk": "ingredient_id",
        "cols": "ingredient_id, ingredient_name, ingredient_value, ingredient_type",
        "search": ["ingredient_name", "ingredient_type"],
        "orders": {"id": "ingredient_id", "alphabet": "ingredient_name", "value": "ingredient_value DESC NULLS LAST, ingredient_name",
                   "type": "ingredient_type, ingredient_name"},
        "sort": {"id": "ingredient_id", "name": "ingredient_name", "value": "ingredient_value",
                 "type": "ingredient_type"},
        "web": "ingredient_id IN (SELECT mi.ingredient_id FROM med_ingredient mi JOIN med m ON m.med_id = mi.med_id WHERE m.in_web)",
        "local": "ingredient_id IN (SELECT mi.ingredient_id FROM med_ingredient mi JOIN stock s ON s.med_id = mi.med_id "
                 "WHERE s.stock_type = 'local' AND s.pharmacy_id = %(pid)s)",
    },
    "illness": {
        "pk": "illness_id",
        "cols": "illness_id, illness_name, illness_type, illness_danger_level, illness_pre_required",
        "search": ["illness_name", "illness_type"],
        "orders": {"id": "illness_id", "alphabet": "illness_name",
                   "value": "CASE illness_danger_level WHEN 'high' THEN 0 WHEN 'moderate' THEN 1 "
                            "WHEN 'low' THEN 2 ELSE 3 END, illness_name"},
        "sort": {"id": "illness_id", "name": "illness_name", "type": "illness_type",
                 "danger": "CASE illness_danger_level WHEN 'low' THEN 0 WHEN 'moderate' THEN 1 "
                           "WHEN 'high' THEN 2 ELSE 3 END",
                 "rx": "illness_pre_required"},
        "web": "illness_id IN (SELECT illness_id FROM med WHERE in_web UNION SELECT mi.illness_id FROM med_illness mi JOIN med m ON m.med_id = mi.med_id WHERE m.in_web)",
        "local": "illness_id IN (SELECT m.illness_id FROM med m JOIN stock s ON s.med_id = m.med_id "
                 "WHERE s.stock_type = 'local' AND s.pharmacy_id = %(pid)s "
                 "UNION SELECT mi.illness_id FROM med_illness mi JOIN stock s ON s.med_id = mi.med_id "
                 "WHERE s.stock_type = 'local' AND s.pharmacy_id = %(pid)s)",
    },
}


WEB_TABLES = {
    "pharma": {
        "pk": "pharma_id", "search": ["pharma_name"],
        "from": "(SELECT p.pharma_id, p.pharma_name, COUNT(*) AS med_count, "
                "COUNT(*) FILTER (WHERE m.prescription_required) AS rx_count "
                "FROM pharma p JOIN med m ON m.pharma_id = p.pharma_id AND m.in_web "
                "GROUP BY p.pharma_id, p.pharma_name) t",
        "orders": {"id": "pharma_id", "alphabet": "pharma_name", "count": "med_count DESC, pharma_name"},
    },
    "ingredient": {
        "pk": "ingredient_id", "search": ["ingredient_name"],
        "from": "(SELECT i.ingredient_id, i.ingredient_name, COUNT(*) AS med_count "
                "FROM ingredient i JOIN med_ingredient mi ON mi.ingredient_id = i.ingredient_id "
                "JOIN med m ON m.med_id = mi.med_id AND m.in_web "
                "GROUP BY i.ingredient_id, i.ingredient_name) t",
        "orders": {"id": "ingredient_id", "alphabet": "ingredient_name", "count": "med_count DESC, ingredient_name"},
    },
    "drugclass": {
        "pk": "class_id", "search": ["class_name"],
        "from": "(SELECT ROW_NUMBER() OVER (ORDER BY type) AS class_id, type AS class_name, COUNT(*) AS med_count, "
                "COUNT(*) FILTER (WHERE prescription_required) AS rx_count "
                "FROM med WHERE in_web AND type IS NOT NULL GROUP BY type) t",
        "orders": {"id": "class_id", "alphabet": "class_name", "count": "med_count DESC, class_name"},
    },
}


def list_web_table(name):
    t = WEB_TABLES[name]
    per_page = int_arg("per_page", 10, hi=PAGE_SIZE_MAX)
    page = int_arg("page", 1)
    params = {"limit": per_page, "offset": (page - 1) * per_page}
    where = ""
    q = request.args.get("q", "").strip()
    if q:
        params["like"] = f"%{q}%"
        where = "WHERE " + " OR ".join(f"{c} ILIKE %(like)s" for c in t["search"])
        m = re.fullmatch(r"[a-zA-Z]*0*(\d+)", q)
        if m:
            params["qid"] = int(m.group(1))
            where += f" OR {t['pk']} = %(qid)s"
    order = t["orders"].get(request.args.get("order", "id"), t["orders"]["id"])
    sql = (f"SELECT *, COUNT(*) OVER () AS total FROM {t['from']} {where} "
           f"ORDER BY {order} LIMIT %(limit)s OFFSET %(offset)s")
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    total = rows[0]["total"] if rows else 0
    for r in rows:
        r.pop("total")
    return jsonify(rows=rows_json(rows), total=total, page=page, per_page=per_page)


@app.get("/api/table/<name>")
def list_table(name):
    if request.args.get("stock") != "local" and name in WEB_TABLES:
        return list_web_table(name)
    t = TABLES.get(name)
    if not t:
        abort(404)
    per_page = int_arg("per_page", 10, hi=PAGE_SIZE_MAX)
    page = int_arg("page", 1)
    params = {"pid": current_pid(), "limit": per_page, "offset": (page - 1) * per_page}
    where = []
    where.append(t["local"] if request.args.get("stock") == "local" else t["web"])
    q = request.args.get("q", "").strip()
    if q:
        params["like"] = f"%{q}%"
        cond = " OR ".join(f"{c} ILIKE %(like)s" for c in t["search"])
        m = re.fullmatch(r"[a-zA-Z]*0*(\d+)", q)
        if m:
            params["qid"] = int(m.group(1))
            cond += f" OR {t['pk']} = %(qid)s"
        where.append(f"({cond})")
    order = t["orders"].get(request.args.get("order", "id"), t["orders"]["id"])
    sort = request.args.get("sort")
    if sort in t["sort"]:
        direction = "DESC" if request.args.get("dir") == "desc" else "ASC"
        order = f"{t['sort'][sort]} {direction} NULLS LAST, {t['pk']}"
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = (f"SELECT {t['cols']}, COUNT(*) OVER () AS total FROM {name} {where_sql} "
           f"ORDER BY {order} LIMIT %(limit)s OFFSET %(offset)s")
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
    total = rows[0]["total"] if rows else 0
    for r in rows:
        r.pop("total")
    return jsonify(rows=rows_json(rows), total=total, page=page, per_page=per_page)


# --------------------------------------------------------------------------- adding rows

def as_bool(v):
    return str(v).strip().lower() in {"true", "yes", "y", "1", "t", "rx"}


def as_num(v, kind=float):
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip().replace(" ", "")
    if "," in s and "." not in s and re.fullmatch(r"-?\d+,\d{1,2}", s):
        s = s.replace(",", ".")  # European decimal comma: "1,5"
    return kind(float(s.replace(",", ""))) if kind is int else kind(s.replace(",", ""))


def as_date(v):
    if v is None or str(v).strip() == "":
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v).strip()[:10])


def get_or_create(cur, table, pk, name_col, name, extra=None):
    if not name:
        return None
    cur.execute(f"SELECT {pk} AS id FROM {table} WHERE LOWER({name_col}) = LOWER(%s)", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    new_id = next_id(cur, table, pk)
    extra = extra or {}
    cols = [pk, name_col, *extra.keys()]
    cur.execute(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
        (new_id, name, *extra.values()),
    )
    return new_id


def save_med(cur, data, stock, pharmacy_id):
    """Insert a medicine (or reuse one with the same name) and, for local stock, upsert its stock row.

    Returns "added" or "updated".
    """
    name = (data.get("med_name") or "").strip()
    if not name:
        raise ValueError("medicine name is missing")
    price = as_num(data.get("price")) or 0
    qty = int(as_num(data.get("quantity")) or 0)
    expiry = as_date(data.get("expiry_date"))
    pharma_id = get_or_create(cur, "pharma", "pharma_id", "pharma_name", (data.get("pharma_name") or "").strip(),
                              {"pharma_country": (data.get("pharma_country") or "").strip() or None})
    illness_id = get_or_create(cur, "illness", "illness_id", "illness_name",
                               (data.get("illness_name") or "").strip())

    cur.execute("SELECT med_id, in_web FROM med WHERE LOWER(med_name) = LOWER(%s) LIMIT 1", (name,))
    found = cur.fetchone()
    status = "updated" if found else "added"
    if found:
        med_id = found["med_id"]
        if stock == "web":
            status = "updated" if found["in_web"] else "added"
            cur.execute("UPDATE med SET price = %s, quantity = %s, expiry_date = COALESCE(%s, expiry_date), "
                        "in_web = TRUE WHERE med_id = %s", (price, qty, expiry, med_id))
    else:
        med_id = next_id(cur, "med", "med_id")
        cur.execute(
            """INSERT INTO med (med_id, med_name, price, quantity, illness_id, type, form, pharma_id,
                                dosage_strength, expiry_date, prescription_required, in_web)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (med_id, name[:250], price, qty if stock == "web" else 0, illness_id,
             (data.get("type") or "").strip() or None, (data.get("form") or "").strip() or None, pharma_id,
             (data.get("dosage_strength") or "").strip() or None, expiry,
             as_bool(data.get("prescription_required")), stock == "web"),
        )
        if illness_id:
            cur.execute("INSERT INTO med_illness (med_id, illness_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (med_id, illness_id))
        for ing in re.split(r"[;,|]", data.get("ingredients") or ""):
            ing = ing.strip()
            if ing:
                ing_id = get_or_create(cur, "ingredient", "ingredient_id", "ingredient_name", ing)
                cur.execute("INSERT INTO med_ingredient (med_id, ingredient_id) VALUES (%s, %s) "
                            "ON CONFLICT DO NOTHING", (med_id, ing_id))
        times = as_num(data.get("times_per_day"), int)
        if times:
            cur.execute("INSERT INTO dosage (dosage_id, med_id, age_group, dosage_note, times_per_day) "
                        "VALUES (%s, %s, 'adult', %s, %s)",
                        (next_id(cur, "dosage", "dosage_id"), med_id, "added by hand", min(max(times, 1), 10)))

    if stock == "local":
        cur.execute("SELECT stock_id FROM stock WHERE pharmacy_id = %s AND med_id = %s AND stock_type = 'local'",
                    (pharmacy_id, med_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE stock SET quantity = %s, unit_price = %s, expiry_date = COALESCE(%s, expiry_date) "
                        "WHERE stock_id = %s", (qty, price, expiry, row["stock_id"]))
            status = "updated"
        else:
            cur.execute("INSERT INTO stock (stock_id, pharmacy_id, med_id, stock_type, quantity, expiry_date, "
                        "unit_price) VALUES (%s, %s, %s, 'local', %s, %s, %s)",
                        (next_id(cur, "stock", "stock_id"), pharmacy_id, med_id, qty, expiry, price))
            status = "added"
    return status


@app.post("/api/meds")
def add_med():
    data = request.json or {}
    stock = "local" if data.get("stock") == "local" else "web"
    pid = current_pid()
    try:
        with db() as conn:
            cur = conn.cursor()
            status = save_med(cur, data, stock, pid)
            if stock == "web":
                cur.execute(WEB_NUMBER_SQL)
            log(cur, pid, stock, "add" if status == "added" else "edit",
                f"{'Added' if status == 'added' else 'Updated'} medicine “{data.get('med_name', '').strip()}” by hand")
    except (ValueError, psycopg.Error) as e:
        return jsonify(error=str(e).split("\n")[0]), 400
    return jsonify(status=status)


# Web Stock has its own numbering (1, 2, 3 ...) separate from the shared med_id.
WEB_NUMBER_SQL = """WITH base AS (SELECT COALESCE(MAX(web_id), 0) AS b FROM med),
     todo AS (SELECT med_id, ROW_NUMBER() OVER (ORDER BY med_id) AS rn FROM med WHERE in_web AND web_id IS NULL)
UPDATE med m SET web_id = (SELECT b FROM base) + todo.rn FROM todo WHERE m.med_id = todo.med_id"""


EDITABLE = {"price": "price", "quantity": "quantity", "expiry_date": "expiry_date"}


@app.patch("/api/meds/<int:med_id>")
def edit_med(med_id):
    """Inline edit of price / quantity / expiry date from the table."""
    data = request.json or {}
    field = data.get("field")
    if field not in EDITABLE:
        return jsonify(error="This column can't be edited"), 400
    stock = "local" if data.get("stock") == "local" else "web"
    if stock == "web":
        return jsonify(error="Web Stock is read-only — it is the national price list"), 400
    pid = current_pid()
    try:
        if field == "price":
            value = as_num(data.get("value"))
            if value is None or value < 0:
                raise ValueError("Price must be 0 or more")
        elif field == "quantity":
            value = as_num(data.get("value"), int)
            if value is None or value < 0:
                raise ValueError("Quantity must be 0 or more")
        else:
            value = as_date(data.get("value"))
    except ValueError as e:
        return jsonify(error=str(e) if "must" in str(e) else "Invalid value"), 400

    if stock == "local":
        col = {"price": "unit_price", "quantity": "quantity", "expiry_date": "expiry_date"}[field]
        old_sql = (f"SELECT m.med_name, s.{col} AS old FROM stock s JOIN med m ON m.med_id = s.med_id "
                   "WHERE s.med_id = %s AND s.pharmacy_id = %s AND s.stock_type = 'local'")
        upd_sql = f"UPDATE stock SET {col} = %s WHERE med_id = %s AND pharmacy_id = %s AND stock_type = 'local'"
        args = (med_id, pid)
    else:
        old_sql = f"SELECT med_name, {field} AS old FROM med WHERE med_id = %s AND in_web"
        upd_sql = f"UPDATE med SET {field} = %s WHERE med_id = %s"
        args = (med_id,)
    with db() as conn:
        cur = conn.cursor()
        cur.execute(old_sql, args)
        row = cur.fetchone()
        if not row:
            return jsonify(error="Medicine not found in this stock"), 404
        cur.execute(upd_sql, (value, *args))
        label = {"price": "price", "quantity": "quantity", "expiry_date": "expiry date"}[field]
        log(cur, pid, stock, "edit",
            f"Changed {label} of “{row['med_name']}” from {show(row['old'])} to {show(value)}")
    return jsonify(status="saved", value=to_json(value))


@app.get("/api/history")
def history():
    pid = current_pid()
    stock = "local" if request.args.get("stock") == "local" else "web"
    with db() as conn:
        rows = conn.execute(
            "SELECT action, summary, created_at AS at FROM history "
            "WHERE pharmacy_id = %s AND stock_type = %s ORDER BY created_at DESC, history_id DESC LIMIT 300",
            (pid, stock),
        ).fetchall()
    return jsonify(rows_json(rows))


@app.post("/api/stock/clear")
def clear_stock():
    data = request.json or {}
    pid = current_pid()
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT pharmacy_name FROM pharmacy WHERE pharmacy_id = %s", (pid,))
        row = cur.fetchone()
        if not row:
            return jsonify(error="Pharmacy not found"), 404
        if (data.get("confirm") or "").strip().lower() != row["pharmacy_name"].strip().lower():
            return jsonify(error="Type the pharmacy name exactly to confirm"), 400
        cur.execute("DELETE FROM stock WHERE pharmacy_id = %s AND stock_type = 'local'", (pid,))
        n = cur.rowcount
        log(cur, pid, "local", "delete", f"Deleted the whole local stock: {n} medicines")
    return jsonify(deleted=n)


TABLE_FIELDS = {
    "pharma": ("pharma_id", ["pharma_name", "pharma_country", "pharma_market_value", "pharma_origin_year"]),
    "ingredient": ("ingredient_id", ["ingredient_name", "ingredient_value", "ingredient_type"]),
    "illness": ("illness_id", ["illness_name", "illness_type", "illness_danger_level", "illness_pre_required"]),
}


@app.post("/api/table/<name>")
def add_row(name):
    if name not in TABLE_FIELDS:
        abort(404)
    pk, fields = TABLE_FIELDS[name]
    data = request.json or {}
    if not str(data.get(fields[0], "")).strip():
        return jsonify(error="Name is required"), 400
    values = []
    for f in fields:
        v = data.get(f)
        if f.endswith("pre_required"):
            v = as_bool(v)
        elif f in ("pharma_market_value", "ingredient_value"):
            v = as_num(v)
        elif f == "pharma_origin_year":
            v = as_num(v, int)
        else:
            v = (str(v).strip() or None) if v is not None else None
        values.append(v)
    try:
        with db() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT 1 FROM {name} WHERE LOWER({fields[0]}) = LOWER(%s)", (values[0],))
            if cur.fetchone():
                return jsonify(error=f"'{values[0]}' already exists"), 400
            new_id = next_id(cur, name, pk)
            cur.execute(f"INSERT INTO {name} ({pk}, {', '.join(fields)}) VALUES ({', '.join(['%s'] * (len(fields) + 1))})",
                        (new_id, *values))
            log(cur, current_pid(), data.get("stock"), "add",
                f"Added {name} “{values[0]}” by hand")
    except (ValueError, psycopg.Error) as e:
        return jsonify(error=str(e).split("\n")[0]), 400
    return jsonify(status="added", id=new_id)


# --------------------------------------------------------------------------- import / export

HEADER_ALIASES = {
    "med_name": ["med_name", "name", "medicine", "medicine_name", "med", "drug", "drug_name", "product"],
    "price": ["price", "unit_price", "cost"],
    "quantity": ["quantity", "qty", "local_qty", "stock", "amount", "count"],
    "illness_name": ["illness", "illness_name", "condition", "disease", "indication"],
    "type": ["type", "med_type", "category", "class"],
    "form": ["form", "dosage_form"],
    "pharma_name": ["pharma", "pharma_name", "manufacturer", "company", "brand"],
    "pharma_country": ["country", "pharma_country", "origin"],
    "ingredients": ["ingredients", "ingredient", "active_ingredient", "composition"],
    "dosage_strength": ["dosage", "dosage_strength", "strength", "dose"],
    "times_per_day": ["schedule", "times_per_day", "frequency"],
    "expiry_date": ["expiry_date", "expiry", "exp", "expiration", "expiration_date"],
    "prescription_required": ["rx", "rx_required", "pre_required", "prescription", "prescription_required"],
}
ALIAS_LOOKUP = {a: key for key, aliases in HEADER_ALIASES.items() for a in aliases}


def norm_header(h):
    return re.sub(r"[^a-z0-9]+", "_", str(h or "").strip().lower()).strip("_")


def read_upload(file):
    """Return (headers, rows) from a .csv / .txt / .tsv / .xlsx upload."""
    filename = (file.filename or "").lower()
    raw = file.read()
    if filename.endswith((".xlsx", ".xlsm")):
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        rows = [list(r) for r in wb.active.iter_rows(values_only=True) if any(c is not None for c in r)]
    else:
        text = raw.decode("utf-8-sig", errors="replace")
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    if not rows:
        raise ValueError("The file is empty")
    return rows[0], rows[1:]


@app.post("/api/import")
def import_stock():
    file = request.files.get("file")
    pharmacy_id = current_pid()
    stock = "local" if request.form.get("stock", "local") == "local" else "web"
    if not file:
        return jsonify(error="No file uploaded"), 400
    try:
        headers, rows = read_upload(file)
    except Exception as e:  # noqa: BLE001 — any parse failure is reported to the user
        return jsonify(error=f"Could not read the file: {e}"), 400
    mapping = {i: ALIAS_LOOKUP.get(norm_header(h)) for i, h in enumerate(headers)}
    if "med_name" not in mapping.values():
        return jsonify(error="The file needs a 'name' (or 'med_name') column. Found: " + ", ".join(map(str, headers))), 400

    counts = {"added": 0, "updated": 0, "skipped": 0}
    errors = []
    with db() as conn:
        for n, row in enumerate(rows, start=2):
            data = {mapping[i]: v for i, v in enumerate(row) if mapping.get(i) and v is not None}
            try:
                with conn.transaction():
                    counts[save_med(conn.cursor(), data, stock, pharmacy_id)] += 1
            except (ValueError, TypeError, psycopg.Error) as e:
                counts["skipped"] += 1
                if len(errors) < 5:
                    errors.append(f"Row {n}: {str(e).splitlines()[0]}")
        conn.execute(
            "INSERT INTO import_batch (import_batch_id, source_name, source_type, record_count, import_date, notes) "
            "VALUES ((SELECT COALESCE(MAX(import_batch_id), 0) + 1 FROM import_batch), %s, %s, %s, CURRENT_DATE, %s)",
            (file.filename[:200], "upload", counts["added"] + counts["updated"], f"{stock} stock, pharmacy {pharmacy_id}"),
        )
        log(conn.cursor(), pharmacy_id, stock, "import",
            f"Imported “{file.filename}”: {counts['added']} added, {counts['updated']} updated, "
            f"{counts['skipped']} skipped")
    return jsonify(**counts, errors=errors, mapped=[h for i, h in enumerate(headers) if mapping.get(i)])


EXPORT_SQL = {
    "med": """SELECT m.med_id, m.med_name, COALESCE(s.unit_price, m.price) AS price, s.quantity,
                     il.illness_name AS illness, m.type, m.form, p.pharma_name AS pharma, p.pharma_country AS country,
                     (SELECT string_agg(i.ingredient_name, '; ' ORDER BY i.ingredient_name)
                        FROM med_ingredient mi JOIN ingredient i ON i.ingredient_id = mi.ingredient_id
                       WHERE mi.med_id = m.med_id) AS ingredients,
                     m.dosage_strength AS dosage, COALESCE(s.expiry_date, m.expiry_date) AS expiry_date,
                     m.prescription_required
              FROM stock s JOIN med m ON m.med_id = s.med_id
              LEFT JOIN illness il ON il.illness_id = m.illness_id
              LEFT JOIN pharma p ON p.pharma_id = m.pharma_id
              WHERE s.stock_type = 'local' AND s.pharmacy_id = %(pid)s ORDER BY m.med_id""",
}
for _name, _t in TABLES.items():
    EXPORT_SQL[_name] = f"SELECT {_t['cols']} FROM {_name} WHERE {_t['local']} ORDER BY {_t['pk']}"
EXPORT_SQL["watchlist"] = f"""
    SELECT {WATCH_LEVEL} AS level, med_id, med_name, form, quantity, {STOCK_STATUS} AS stock_status,
           expiry_date, {EXPIRY_STATUS} AS expiry_status, price, pharma_name AS pharma, pharma_country AS country
    FROM ({med_base("local", None, None, None)}) b
    WHERE {WATCH_WHERE}
    ORDER BY CASE WHEN {WATCH_LEVEL} = 'red' THEN 0 ELSE 1 END, med_id"""


EXPORT_LABELS = {"watchlist": "Watchlist", "med": "Medicine", "pharma": "Pharma", "ingredient": "Ingredient", "illness": "Illness"}


@app.get("/api/export")
def export_stock():
    pid = current_pid()
    tables = [t for t in request.args.get("tables", "med").split(",") if t in EXPORT_SQL]
    if not tables:
        return jsonify(error="Choose at least one table"), 400
    files = {}
    with db() as conn:
        for t in tables:
            cur = conn.execute(EXPORT_SQL[t], {"pid": pid})
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow([c.name for c in cur.description])
            for r in cur.fetchall():
                w.writerow([to_json(v) for v in r.values()])
            files[f"{t}.csv"] = buf.getvalue()
        log(conn.cursor(), pid, "local", "download",
            "Downloaded " + ", ".join(EXPORT_LABELS[t] for t in tables) + " table" + ("s" if len(tables) > 1 else ""))
    if len(files) == 1:
        name, content = next(iter(files.items()))
        return send_file(io.BytesIO(content.encode("utf-8-sig")), mimetype="text/csv",
                         as_attachment=True, download_name=f"local_stock_{name}")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content.encode("utf-8-sig"))
    mem.seek(0)
    return send_file(mem, mimetype="application/zip", as_attachment=True, download_name="local_stock.zip")


if __name__ == "__main__":
    # Local development server. Online, Render starts the app with gunicorn instead (see render.yaml).
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1")
