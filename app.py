from __future__ import annotations

import json
import os
import socket
import sqlite3
import sys
from datetime import date, datetime
from functools import wraps
from math import ceil
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()

def get_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # When frozen, we want the database to be next to the executable, 
        # not inside the temporary internal _MEIPASS folder.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

DATA_DIR = get_data_dir()

DB_PATH = DATA_DIR / "receipts.db"
BRANDING_CONFIG_PATH = DATA_DIR / "branding.json"
CONFIG_PATH = DATA_DIR / "app_config.json"

app = Flask(__name__, 
            template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))
app.config["SECRET_KEY"] = os.getenv("RECEIPT_SECRET_KEY", "change-this-secret")
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7  # 7 days
# Allow larger payloads for high-resolution PNG/PDF exports
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
DEFAULT_SID = "GENERAL"


def load_branding() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "clinic_name": "DENTALCARE",
        "clinic_tagline": "Lorem ipsum dolor sit",
        "document_title_small": "MEDICAL",
        "document_title_big": "INVOICE",
        "logo_url": "",
        "address_lines": [
            "Address",
            "yourmail@example.com",
            "1234 - 8989 8899",
            "www.example.com",
        ],
        "social_lines": [
            "@youraccount",
            "@youraccount",
            "@youraccount",
        ],
        "terms_title": "Terms & Conditions",
        "terms_text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat.",
    }

    if not BRANDING_CONFIG_PATH.exists():
        # Try looking in BASE_DIR if not in DATA_DIR (for the first run/fresh install)
        alt_path = BASE_DIR / "branding.json"
        if alt_path.exists():
            try:
                loaded = json.loads(alt_path.read_text(encoding="utf-8"))
                # Copy it to DATA_DIR so it can be modified if needed
                BRANDING_CONFIG_PATH.write_text(json.dumps(loaded, indent=2), encoding="utf-8")
                return loaded
            except:
                pass
        return defaults

    try:
        loaded = json.loads(BRANDING_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return defaults

    if not isinstance(loaded, dict):
        return defaults

    merged = defaults.copy()
    merged.update(loaded)
    return merged


def get_lan_ip() -> str:
    """Get the local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def load_app_config() -> dict[str, Any]:
    """Load or create app configuration (password, etc)."""
    defaults = {
        "password": "password",
        "password_enabled": True,
    }
    
    if not CONFIG_PATH.exists():
        return defaults
    
    try:
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return defaults
    
    if not isinstance(loaded, dict):
        return defaults
    
    merged = defaults.copy()
    merged.update(loaded)
    return merged


def save_app_config(config: dict[str, Any]) -> None:
    """Save app configuration."""
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def require_password(func):
    """Decorator to require password authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return wrapper


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
    backfill_sql: str | None = None,
) -> None:
    if _column_exists(conn, table, column):
        return

    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    if backfill_sql:
        conn.execute(backfill_sql)


def init_db() -> None:
    # Ensure DATA_DIR exists
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to current directory if DATA_DIR creation fails
        pass
    
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sids (
                sid TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_receipt_number TEXT
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                created_at TEXT NOT NULL,
                last_used TEXT,
                times_used INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT UNIQUE NOT NULL COLLATE NOCASE,
                price REAL NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT,
                times_used INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                sid TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                tax_rate REAL NOT NULL DEFAULT 0,
                subtotal REAL NOT NULL,
                tax REAL NOT NULL,
                total REAL NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (sid) REFERENCES sids(sid)
            );

            CREATE TABLE IF NOT EXISTS receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
            );
            """
        )

        # Keep older local databases compatible with newer queries/routes.
        _ensure_column(
            conn,
            "customers",
            "created_at",
            "TEXT",
            "UPDATE customers SET created_at = datetime('now') WHERE created_at IS NULL OR created_at = ''",
        )
        _ensure_column(
            conn,
            "customers",
            "last_used",
            "TEXT",
            "UPDATE customers SET last_used = created_at WHERE last_used IS NULL OR last_used = ''",
        )
        _ensure_column(
            conn,
            "customers",
            "times_used",
            "INTEGER DEFAULT 1",
            "UPDATE customers SET times_used = 1 WHERE times_used IS NULL OR times_used < 0",
        )

        _ensure_column(
            conn,
            "items",
            "created_at",
            "TEXT",
            "UPDATE items SET created_at = datetime('now') WHERE created_at IS NULL OR created_at = ''",
        )
        _ensure_column(
            conn,
            "items",
            "last_used",
            "TEXT",
            "UPDATE items SET last_used = created_at WHERE last_used IS NULL OR last_used = ''",
        )
        _ensure_column(
            conn,
            "items",
            "times_used",
            "INTEGER DEFAULT 1",
            "UPDATE items SET times_used = 1 WHERE times_used IS NULL OR times_used < 0",
        )

        _ensure_column(conn, "receipts", "created_at", "TEXT")
        _ensure_column(conn, "receipts", "notes", "TEXT")
        _ensure_column(conn, "sids", "last_receipt_number", "TEXT")


def parse_float(value: str, default: float = 0.0) -> float:
    text = (value or "").strip().replace(",", "")
    if not text:
        return default
    return float(text)


def parse_int(value: str, default: int = 1) -> int:
    text = (value or "").strip().replace(",", "")
    if not text:
        return default
    return int(text)


def get_pagination_params(default_per_page: int = 20, max_per_page: int = 100) -> tuple[int, int]:
    page_raw = request.args.get("page", "1")
    per_page_raw = request.args.get("per_page", str(default_per_page))

    try:
        page = max(1, int(page_raw))
    except ValueError:
        page = 1

    try:
        per_page = int(per_page_raw)
    except ValueError:
        per_page = default_per_page

    per_page = max(1, min(max_per_page, per_page))
    return page, per_page


def make_pagination(total: int, page: int, per_page: int) -> dict[str, Any]:
    total_pages = max(1, ceil(total / per_page)) if total > 0 else 1
    page = max(1, min(page, total_pages))
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }


def make_receipt_number(receipt_id: int) -> str:
    return f"INV-{receipt_id:05d}"


@app.template_filter("iqd")
def format_iqd(value: Any) -> str:
    try:
        amount = int(round(float(value)))
    except (TypeError, ValueError):
        amount = 0
    return f"{amount:,} IQD"


@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    branding = load_branding()
    return {
        "lan_ip": get_lan_ip(),
        "app_port": int(os.getenv("RECEIPT_PORT", "80")),
        "branding": branding,
    }


def resolve_logo_src(logo_url: str) -> str:
    raw = (logo_url or "").strip()
    if not raw:
        return ""

    normalized = raw.replace("\\", "/")

    if normalized.startswith(("http://", "https://", "data:", "/img/", "/logo-local")):
        return normalized

    if normalized.startswith("img/"):
        return url_for("serve_img", filename=normalized[4:])

    if "/" not in normalized and ":" not in normalized:
        return url_for("serve_img", filename=normalized)

    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()

    if path.exists() and path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
        return url_for("serve_local_logo", path=str(path))

    return ""


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    app_config = load_app_config()
    
    if not app_config.get("password_enabled", True):
        session["authenticated"] = True
        return redirect(request.args.get("next") or url_for("index"))
    
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if password == app_config.get("password", "password"):
            session.permanent = True
            session["authenticated"] = True
            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Incorrect password.", "error")
    
    return render_template("login.html")


@app.route("/logout")
def logout() -> str:
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/settings", methods=["GET", "POST"])
@require_password
def settings() -> str:
    app_config = load_app_config()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "password":
            new_password = (request.form.get("new_password") or "").strip()
            if len(new_password) < 4:
                flash("Password must be at least 4 characters.", "error")
            else:
                app_config["password"] = new_password
                save_app_config(app_config)
                flash("Password updated successfully.", "success")
        
        elif action == "toggle_auth":
            app_config["password_enabled"] = not app_config.get("password_enabled", True)
            save_app_config(app_config)
            status = "enabled" if app_config["password_enabled"] else "disabled"
            flash(f"Password protection {status}.", "success")
    
    app_config = load_app_config()
    lan_ip = get_lan_ip()
    app_port = int(os.getenv("RECEIPT_PORT", "81"))
    
    return render_template("settings.html", lan_ip=lan_ip, app_port=app_port, app_config=app_config)


@app.route("/", methods=["GET", "POST"])
@require_password
def index() -> str:
    if request.method == "POST":
        sid = DEFAULT_SID
        customer_name = (request.form.get("customer_name") or "").strip()
        invoice_date = (request.form.get("invoice_date") or str(date.today())).strip()
        notes = (request.form.get("notes") or "").strip()

        if not customer_name:
            flash("Customer name is required.", "error")
            return render_template("index.html", today=str(date.today()))

        descriptions = request.form.getlist("description[]")
        quantities = request.form.getlist("qty[]")
        prices = request.form.getlist("price[]")

        items: list[dict[str, Any]] = []
        for description, qty_raw, price_raw in zip(descriptions, quantities, prices):
            description = (description or "").strip()
            if not description:
                continue
            try:
                qty = parse_int(qty_raw, 1)
                price = parse_float(price_raw, 0.0)
            except ValueError:
                flash("Please use a whole number for quantity and a valid number for price.", "error")
                return render_template("index.html", today=str(date.today()))

            if qty <= 0:
                flash("Quantity must be at least 1.", "error")
                return render_template("index.html", today=str(date.today()))

            line_total = round(qty * price, 2)
            items.append(
                {
                    "description": description,
                    "qty": qty,
                    "price": round(price, 0),
                    "line_total": line_total,
                }
            )

        if not items:
            flash("Please add at least one item.", "error")
            return render_template("index.html", today=str(date.today()))

        subtotal = round(sum(item["line_total"] for item in items), 2)
        tax_rate = 0.0
        tax = 0.0
        total = subtotal
        created_at = datetime.utcnow().isoformat(timespec="seconds")

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO sids (sid, created_at, last_receipt_number)
                VALUES (?, ?, '')
                ON CONFLICT(sid) DO NOTHING
                """,
                (sid, created_at),
            )

            conn.execute(
                """
                INSERT INTO customers (name, created_at, last_used, times_used)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(name) DO UPDATE SET
                    last_used = excluded.last_used,
                    times_used = times_used + 1
                """,
                (customer_name, created_at, created_at),
            )

            cursor = conn.execute(
                """
                INSERT INTO receipts (
                    receipt_number, sid, customer_name, invoice_date, tax_rate,
                    subtotal, tax, total, notes, created_at
                )
                VALUES ('', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, customer_name, invoice_date, tax_rate, subtotal, tax, total, notes, created_at),
            )
            receipt_id = int(cursor.lastrowid)
            receipt_number = make_receipt_number(receipt_id)

            conn.execute(
                "UPDATE receipts SET receipt_number = ? WHERE id = ?",
                (receipt_number, receipt_id),
            )

            conn.execute(
                "UPDATE sids SET last_receipt_number = ? WHERE sid = ?",
                (receipt_number, sid),
            )

            conn.executemany(
                """
                INSERT INTO receipt_items (receipt_id, description, qty, price, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        receipt_id,
                        item["description"],
                        item["qty"],
                        item["price"],
                        item["line_total"],
                    )
                    for item in items
                ],
            )

            # Save items to items table (first-use pattern)
            for item in items:
                conn.execute(
                    """
                    INSERT INTO items (description, price, created_at, last_used, times_used)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(description) DO UPDATE SET
                        last_used = excluded.last_used,
                        times_used = times_used + 1,
                        price = excluded.price
                    """,
                    (item["description"], item["price"], created_at, created_at),
                )

        return redirect(url_for("view_receipt", receipt_id=receipt_id))

    return render_template("index.html", today=str(date.today()))


@app.route("/api/customers")
def get_customers():
    with get_db() as conn:
        customers = conn.execute(
            "SELECT DISTINCT name FROM customers ORDER BY last_used DESC, times_used DESC LIMIT 100",
        ).fetchall()
    return [row[0] for row in customers]


@app.route("/api/items")
def get_items():
    with get_db() as conn:
        items = conn.execute(
            "SELECT description FROM items ORDER BY last_used DESC, times_used DESC LIMIT 100",
        ).fetchall()
    return [row[0] for row in items]


@app.route("/api/items-with-prices")
def get_items_with_prices():
    with get_db() as conn:
        items = conn.execute(
            "SELECT description, price FROM items ORDER BY last_used DESC, times_used DESC LIMIT 100",
        ).fetchall()
    return [{"description": row[0], "price": row[1]} for row in items]


@app.route("/customers")
@require_password
def customers_list():
    page, per_page = get_pagination_params(default_per_page=20)
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        pagination = make_pagination(total, page, per_page)
        offset = (pagination["page"] - 1) * pagination["per_page"]
        customers = conn.execute(
            """
            SELECT name, times_used, last_used
            FROM customers
            ORDER BY last_used DESC, times_used DESC
            LIMIT ? OFFSET ?
            """,
            (pagination["per_page"], offset),
        ).fetchall()
    return render_template("customers.html", customers=customers, pagination=pagination)


@app.route("/customer/<name>/receipts")
@require_password
def customer_receipts(name: str):
    page, per_page = get_pagination_params(default_per_page=20)
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM receipts WHERE customer_name = ?",
            (name,),
        ).fetchone()[0]
        pagination = make_pagination(total, page, per_page)
        offset = (pagination["page"] - 1) * pagination["per_page"]
        receipts = conn.execute(
            """
            SELECT id, receipt_number, invoice_date, total
            FROM receipts
            WHERE customer_name = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (name, pagination["per_page"], offset),
        ).fetchall()
    return render_template(
        "customer_receipts.html",
        customer_name=name,
        receipts=receipts,
        pagination=pagination,
    )


@app.route("/items")
@require_password
def items_list():
    page, per_page = get_pagination_params(default_per_page=20)
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        pagination = make_pagination(total, page, per_page)
        offset = (pagination["page"] - 1) * pagination["per_page"]
        items = conn.execute(
            """
            SELECT description, price, times_used, last_used
            FROM items
            ORDER BY last_used DESC, times_used DESC
            LIMIT ? OFFSET ?
            """,
            (pagination["per_page"], offset),
        ).fetchall()
    return render_template("items.html", items=items, pagination=pagination)


@app.route("/item/<item_desc>/receipts")
@require_password
def item_receipts(item_desc: str):
    page, per_page = get_pagination_params(default_per_page=20)
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(DISTINCT receipt_id) FROM receipt_items WHERE description = ?",
            (item_desc,),
        ).fetchone()[0]
        pagination = make_pagination(total, page, per_page)
        offset = (pagination["page"] - 1) * pagination["per_page"]

        receipts = conn.execute(
            """
            SELECT DISTINCT r.id, r.receipt_number, r.invoice_date, r.total, r.customer_name
            FROM receipts r
            INNER JOIN receipt_items ri ON r.id = ri.receipt_id
            WHERE ri.description = ?
            ORDER BY r.id DESC
            LIMIT ? OFFSET ?
            """,
            (item_desc, pagination["per_page"], offset),
        ).fetchall()
    return render_template(
        "item_receipts.html",
        item_description=item_desc,
        receipts=receipts,
        pagination=pagination,
    )


# Customer management routes
@app.route("/customer/delete/<name>", methods=["POST"])
@require_password
def delete_customer(name: str):
    with get_db() as conn:
        conn.execute("DELETE FROM customers WHERE name = ? COLLATE NOCASE", (name,))
    flash(f"Customer '{name}' deleted successfully.", "success")
    return redirect(url_for("customers_list"))


@app.route("/customer/edit/<name>", methods=["GET", "POST"])
@require_password
def edit_customer(name: str):
    if request.method == "POST":
        new_name = (request.form.get("name") or "").strip()

        if not new_name:
            flash("Customer name is required.", "error")
            return redirect(url_for("edit_customer", name=name))

        with get_db() as conn:
            existing = conn.execute(
                "SELECT 1 FROM customers WHERE name = ? COLLATE NOCASE AND name != ? COLLATE NOCASE",
                (new_name, name),
            ).fetchone()
            if existing:
                flash("A customer with this name already exists.", "error")
                return redirect(url_for("edit_customer", name=name))

            conn.execute(
                "UPDATE customers SET name = ? WHERE name = ? COLLATE NOCASE",
                (new_name, name),
            )
            conn.execute(
                "UPDATE receipts SET customer_name = ? WHERE customer_name = ? COLLATE NOCASE",
                (new_name, name),
            )

        flash("Customer updated successfully.", "success")
        return redirect(url_for("customers_list"))

    with get_db() as conn:
        customer = conn.execute(
            "SELECT name, times_used, last_used FROM customers WHERE name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()

    if customer is None:
        return "Customer not found", 404

    return render_template("edit_customer.html", customer=customer)


# Item management routes
@app.route("/item/delete/<item_desc>", methods=["POST"])
@require_password
def delete_item(item_desc: str):
    with get_db() as conn:
        conn.execute("DELETE FROM items WHERE description = ? COLLATE NOCASE", (item_desc,))
    flash(f"Item '{item_desc}' deleted successfully.", "success")
    return redirect(url_for("items_list"))


@app.route("/item/edit/<item_desc>", methods=["GET", "POST"])
@require_password
def edit_item(item_desc: str):
    if request.method == "POST":
        new_description = (request.form.get("description") or "").strip()
        new_price = parse_float(request.form.get("price", "0"), 0.0)
        
        if not new_description:
            flash("Item description is required.", "error")
            return redirect(url_for("edit_item", item_desc=item_desc))
        
        with get_db() as conn:
            conn.execute(
                "UPDATE items SET description = ?, price = ? WHERE description = ? COLLATE NOCASE",
                (new_description, new_price, item_desc),
            )
        flash(f"Item updated successfully.", "success")
        return redirect(url_for("items_list"))
    
    with get_db() as conn:
        item = conn.execute(
            "SELECT description, price FROM items WHERE description = ? COLLATE NOCASE",
            (item_desc,),
        ).fetchone()
    
    if item is None:
        return "Item not found", 404
    
    return render_template("edit_item.html", item=item)


@app.route("/item/add", methods=["GET", "POST"])
@require_password
def add_item():
    if request.method == "POST":
        description = (request.form.get("description") or "").strip()
        price = parse_float(request.form.get("price", "0"), 0.0)
        
        if not description:
            flash("Item description is required.", "error")
            return render_template("add_item.html")
        
        created_at = datetime.utcnow().isoformat(timespec="seconds")
        
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO items (description, price, created_at, last_used, times_used)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(description) DO NOTHING
                """,
                (description, price, created_at, created_at),
            )
        flash(f"Item '{description}' added successfully.", "success")
        return redirect(url_for("items_list"))
    
    return render_template("add_item.html")


@app.route("/customer/add", methods=["GET", "POST"])
@require_password
def add_customer():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        
        if not name:
            flash("Customer name is required.", "error")
            return render_template("add_customer.html")
        
        created_at = datetime.utcnow().isoformat(timespec="seconds")
        
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO customers (name, created_at, last_used, times_used)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(name) DO NOTHING
                """,
                (name, created_at, created_at),
            )
        flash(f"Customer '{name}' added successfully.", "success")
        return redirect(url_for("customers_list"))
    
    return render_template("add_customer.html")


@app.route("/receipt/<int:receipt_id>")
@require_password
def view_receipt(receipt_id: int) -> str:
    with get_db() as conn:
        receipt = conn.execute(
            "SELECT * FROM receipts WHERE id = ?",
            (receipt_id,),
        ).fetchone()

        if receipt is None:
            return "Receipt not found", 404

        items = conn.execute(
            "SELECT description, qty, price, line_total FROM receipt_items WHERE receipt_id = ? ORDER BY id",
            (receipt_id,),
        ).fetchall()

    branding = load_branding()
    logo_src = resolve_logo_src(str(branding.get("logo_url", "")))
    return render_template("receipt.html", receipt=receipt, items=items, branding=branding, logo_src=logo_src)


@app.route("/receipt/<int:receipt_id>/edit", methods=["GET", "POST"])
@require_password
def edit_receipt(receipt_id: int) -> str:
    with get_db() as conn:
        receipt = conn.execute(
            "SELECT * FROM receipts WHERE id = ?",
            (receipt_id,),
        ).fetchone()

    if receipt is None:
        return "Receipt not found", 404

    if request.method == "POST":
        customer_name = (request.form.get("customer_name") or "").strip()
        invoice_date = (request.form.get("invoice_date") or str(date.today())).strip()
        notes = (request.form.get("notes") or "").strip()

        if not customer_name:
            flash("Customer name is required.", "error")
            return redirect(url_for("edit_receipt", receipt_id=receipt_id))

        descriptions = request.form.getlist("description[]")
        quantities = request.form.getlist("qty[]")
        prices = request.form.getlist("price[]")

        items: list[dict[str, Any]] = []
        for description, qty_raw, price_raw in zip(descriptions, quantities, prices):
            description = (description or "").strip()
            if not description:
                continue
            try:
                qty = parse_int(qty_raw, 1)
                price = parse_float(price_raw, 0.0)
            except ValueError:
                flash("Please use a whole number for quantity and a valid number for price.", "error")
                return redirect(url_for("edit_receipt", receipt_id=receipt_id))

            if qty <= 0:
                flash("Quantity must be at least 1.", "error")
                return redirect(url_for("edit_receipt", receipt_id=receipt_id))

            line_total = round(qty * price, 2)
            items.append(
                {
                    "description": description,
                    "qty": qty,
                    "price": round(price, 0),
                    "line_total": line_total,
                }
            )

        if not items:
            flash("Please add at least one item.", "error")
            return redirect(url_for("edit_receipt", receipt_id=receipt_id))

        subtotal = round(sum(item["line_total"] for item in items), 2)
        tax_rate = float(receipt["tax_rate"] or 0)
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)
        used_at = datetime.utcnow().isoformat(timespec="seconds")

        with get_db() as conn:
            conn.execute(
                """
                UPDATE receipts
                SET customer_name = ?, invoice_date = ?, subtotal = ?, tax = ?, total = ?, notes = ?
                WHERE id = ?
                """,
                (customer_name, invoice_date, subtotal, tax, total, notes, receipt_id),
            )

            conn.execute("DELETE FROM receipt_items WHERE receipt_id = ?", (receipt_id,))

            conn.executemany(
                """
                INSERT INTO receipt_items (receipt_id, description, qty, price, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        receipt_id,
                        item["description"],
                        item["qty"],
                        item["price"],
                        item["line_total"],
                    )
                    for item in items
                ],
            )

            conn.execute(
                """
                INSERT INTO customers (name, created_at, last_used, times_used)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(name) DO UPDATE SET
                    last_used = excluded.last_used,
                    times_used = times_used + 1
                """,
                (customer_name, used_at, used_at),
            )

            for item in items:
                conn.execute(
                    """
                    INSERT INTO items (description, price, created_at, last_used, times_used)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(description) DO UPDATE SET
                        last_used = excluded.last_used,
                        times_used = times_used + 1,
                        price = excluded.price
                    """,
                    (item["description"], item["price"], used_at, used_at),
                )

        flash("Receipt updated successfully.", "success")
        return redirect(url_for("view_receipt", receipt_id=receipt_id))

    with get_db() as conn:
        items = conn.execute(
            "SELECT description, qty, price, line_total FROM receipt_items WHERE receipt_id = ? ORDER BY id",
            (receipt_id,),
        ).fetchall()

    return render_template("edit_receipt.html", receipt=receipt, items=items)


@app.route("/img/<path:filename>")
def serve_img(filename: str):
    # First try DATA_DIR (user uploaded/copied logos)
    data_img = DATA_DIR / "img" / filename
    if data_img.exists():
        return send_from_directory(DATA_DIR / "img", filename)
    # Then try BASE_DIR (bundled assets)
    return send_from_directory(BASE_DIR / "img", filename)


@app.route("/logo-local")
def serve_local_logo():
    raw_path = (request.args.get("path") or "").strip()
    if not raw_path:
        return "Not found", 404

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()

    if not path.exists() or not path.is_file() or path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return "Not found", 404

    return send_file(path)


@app.route("/history")
@require_password
def history() -> str:
    page, per_page = get_pagination_params(default_per_page=20)
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
        pagination = make_pagination(total, page, per_page)
        offset = (pagination["page"] - 1) * pagination["per_page"]
        rows = conn.execute(
            """
            SELECT id, receipt_number, customer_name, invoice_date, total
            FROM receipts
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """
            ,
            (pagination["per_page"], offset),
        ).fetchall()

    return render_template("history.html", receipts=rows, pagination=pagination)


@app.route("/receipt/<int:receipt_id>/delete", methods=["POST"])
@require_password
def delete_receipt(receipt_id: int):
    with get_db() as conn:
        receipt = conn.execute(
            "SELECT receipt_number FROM receipts WHERE id = ?",
            (receipt_id,),
        ).fetchone()

        if receipt is None:
            flash("Receipt not found.", "error")
            return redirect(url_for("history"))

        conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))

    flash(f"Receipt {receipt['receipt_number']} deleted successfully.", "success")
    return redirect(url_for("history"))


@app.route("/offline")
def offline() -> str:
    return render_template("offline.html")


@app.route("/api/export-pdf", methods=["POST"])
@require_password
def export_pdf():
    data = request.json
    if not data or "pdf_data" not in data or "filename" not in data:
        return "Invalid data", 400
    
    import base64
    from io import BytesIO
    
    try:
        # Some clients might send just the base64 part, others might send the data URI
        raw_data = data["pdf_data"]
        if "," in raw_data:
            header, encoded = raw_data.split(",", 1)
        else:
            encoded = raw_data
            
        pdf_content = base64.b64decode(encoded)
        return send_file(
            BytesIO(pdf_content),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=data["filename"]
        )
    except Exception as e:
        import traceback
        print(f"PDF Export Error: {e}")
        traceback.print_exc()
        return str(e), 500

@app.route("/api/export-png", methods=["POST"])
@require_password
def export_png():
    data = request.json
    if not data or "png_data" not in data or "filename" not in data:
        return "Invalid data", 400
    
    import base64
    from io import BytesIO
    
    try:
        raw_data = data["png_data"]
        if "," in raw_data:
            header, encoded = raw_data.split(",", 1)
        else:
            encoded = raw_data
            
        png_content = base64.b64decode(encoded)
        return send_file(
            BytesIO(png_content),
            mimetype="image/png",
            as_attachment=True,
            download_name=data["filename"]
        )
    except Exception as e:
        import traceback
        print(f"PNG Export Error: {e}")
        traceback.print_exc()
        return str(e), 500

init_db()


if __name__ == "__main__":
    # Binding to 0.0.0.0 allows LAN access
    host = os.getenv("RECEIPT_HOST", "0.0.0.0")
    port = int(os.getenv("RECEIPT_PORT", "81"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    
    print(f"Starting server on {host}:{port}")
    print(f"Accessible on LAN at http://{get_lan_ip()}:{port}")
    
    app.run(host=host, port=port, debug=debug)
