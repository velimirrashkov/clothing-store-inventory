# Clothing Store Inventory

A local web app for running a clothing store's inventory, purchasing, sales (POS), and reporting — built with FastAPI, SQLAlchemy, SQLite, and server-rendered Jinja2 templates (no JS framework, no build step).

Available in Bulgarian (default) and English, with a language toggle in the nav.

## Features

- **Inventory** — products with size/colour variants, per-variant SKU and barcode, hierarchical categories (unlimited nesting), material/care/season metadata, and free-form attributes. Browsed as a collapsible category tree with a master-detail view (click an item to see its details without leaving the page).
- **Suppliers** — full CRUD, with a per-product vendor catalog (a product can be sourced from multiple suppliers at different quoted costs).
- **Purchase Orders** — draft → ordered → partial/received workflow. Every delivery creates its own stock batch (quantity + price + date), so costing is tracked per delivery rather than a single blended average. Profit on each sale is computed FIFO (oldest batch consumed first).
- **Sell (POS)** — cart-based checkout with a combined search/category-browse dropdown, a running total, and a receipt per sale.
- **Reports** — revenue/cost/profit/margin over a date range, a revenue-by-day chart, top-selling products, and current inventory value.
- **Users & roles** — session-based login. Two roles: **admin** (everything, plus user management) and **sales** (Inventory + Sell only).

## Requirements

- Python 3.9+ (developed against 3.9.2)
- No external database — uses a local SQLite file (`inventory.db`, created automatically)

## Setup

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Windows + Python 3.9 note:** the newest `greenlet` releases no longer ship a prebuilt wheel for Python 3.9 on Windows, which makes a plain `pip install` try to compile it from source and fail without Visual C++ Build Tools. `requirements.txt` pins a version that still has a wheel, so a normal `pip install -r requirements.txt` should just work. If you ever hit a greenlet build error anyway, install it explicitly first: `pip install "greenlet==3.1.1" --only-binary=:all:`, then retry.

## Running

```powershell
.\venv\Scripts\python.exe run.py
```

Then open **http://127.0.0.1:8000**. On first run, with no users in the database, you'll be prompted to create the initial admin account instead of a login form.

## Sample data (optional)

`seed_data.py` populates the database with realistic sample suppliers, products, purchase orders, and sales — useful for trying the app out. It refuses to run against a non-empty database, so it won't duplicate data:

```powershell
.\venv\Scripts\python.exe seed_data.py
```

## Project layout

```
app/
  models.py          SQLAlchemy models
  main.py            FastAPI app, middleware, routers, RBAC wiring
  auth.py            Password hashing, session auth, role-based access dependencies
  i18n.py            Translation strings (BG/EN)
  templating.py      Shared Jinja2 render() helper
  routers/           One module per feature area (inventory, suppliers, purchase_orders, sales, reports, users, categories, auth, lang)
  templates/          Jinja2 templates, mirroring the routers
  static/             CSS and vanilla JS (category tree, cart, inventory master-detail view)
```
