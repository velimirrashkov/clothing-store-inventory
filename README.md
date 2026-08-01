# Clothing Store — Inventory & Webshop

A modular-monolith rebuild of the clothing store's inventory/webshop system, following
[architecture-spec.md](architecture-spec.md). Backend only so far — see "Status" below.

**Stack:** Python 3.12 + Django 5 + Django REST Framework, PostgreSQL 16, Redis 7, Celery.
No frontend yet (React SPA is Phase 2 — see architecture-spec.md §13).

> The previous FastAPI/SQLite/Jinja2 version of this project lives on the `legacy-fastapi`
> branch for reference. It is not being extended further.

## Status: Phase 1 (inventory core)

Implemented, with real Postgres migrations and a passing test suite:

- **accounts** — custom `User` model, session auth (`/api/v1/auth/register|login|logout|me`),
  role groups (`worker`/`manager`/`admin`) seeded from `apps/accounts/roles.py`.
- **catalog** — categories, products, variants (the SKU), full-text + trigram search,
  variant-matrix generation, barcode assignment. Public read API under `/api/v1/products`,
  `/api/v1/categories`.
- **inventory** — the append-only stock ledger (`record_movement`), reservations with TTL
  expiry, stocktakes, nightly ledger/cache reconciliation. This is the part of the spec
  marked "read before changing anything" (§5) — see `apps/inventory/services.py`.
- **audit** — append-only `AuditLog`, written explicitly from services (never via signals).

`orders`, `pricing`, and `customers` exist as schema-only stubs (their tables are FK targets
for `inventory.Reservation` and `orders.Order`'s permissions), with checkout/fulfilment
business logic deferred to Phase 2 per the spec's build order (§13).

## Requirements

- Docker + Docker Compose (runs Python 3.12, Postgres 16, Redis 7 — no local install of any
  of these needed)

## Setup

```powershell
cd backend
cp .env.example .env
docker compose build
docker compose up -d postgres redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_roles
docker compose run --rm web python manage.py seed_default_location
docker compose run --rm web python manage.py createsuperuser
docker compose up -d web
```

The API is then live at **http://localhost:8000/api/v1/** (e.g. `/api/v1/products`,
`/api/v1/categories`). The break-glass Django admin is at `/django-admin-x7q/` — superuser
only, not a daily interface (see architecture-spec.md §9).

Postgres and Redis are also reachable from the host on `localhost:5433` and `localhost:6380`
(shifted off their default ports to avoid clashing with any local install).

## Running tests

```powershell
docker compose run --rm web python -m pytest
docker compose run --rm web ruff check .
```

The highest-priority tests are in `apps/inventory/tests/test_ledger.py` — they include a
multi-threaded test proving concurrent reservations against a single unit of stock cannot
oversell (architecture-spec.md §10.1). `apps/accounts/tests/test_permission_matrix.py` is the
seed of the permission matrix described in §10.2 — add a row for every new endpoint.

## Project layout

```
backend/
  config/               settings (base/dev/prod), urls, celery.py
  apps/
    core/               base models, exceptions, pagination, permissions — no business logic
    accounts/            User, roles, sessions
    catalog/              Product, Variant, Category, search
    inventory/             the stock ledger — see services.py before touching this app
    orders/                schema stub (Cart/Order/OrderLine) — Phase 2
    pricing/               schema stub (Discount) — Phase 2
    customers/              schema stub (Address, CustomerProfile) — Phase 2
    audit/               AuditLog + record()
  docker-compose.yml
  Dockerfile
  requirements/{base,dev,prod}.txt
```

Each app follows the same internal shape (`models.py` / `services.py` / `selectors.py` /
`api/` / `tasks.py` / `admin.py`) described in architecture-spec.md §2.1. The one rule that
keeps it from rotting into a ball of mud: **apps talk to each other only through
`services.py`/`selectors.py`, never by importing another app's models directly** (§2.2).

## What's next

Per architecture-spec.md §13:

- **Phase 1 (this repo, backend)** — accounts, catalog, inventory, audit. ✅ done here.
  Still open: the React back-office (products, variant matrix, stock adjustments, barcode
  lookup, stocktake UI) — "run the real shop on this before writing any storefront code."
- **Phase 2** — storefront (public catalog, cart, checkout with reservations), buyer
  accounts, order history, payments.
- **Phase 3** — returns, refunds, reporting, low-stock automation, purchase orders.
- **Phase 4** — productization (multi-tenant seams, catalog API, per-tenant theming).
