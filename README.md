# Clothing Store — Inventory & Webshop

A modular-monolith rebuild of the clothing store's inventory/webshop system, following an
architecture spec kept locally as `architecture-spec.md` (gitignored — not pushed to GitHub,
since it documents internal security controls like rate limits, session config, and the
break-glass admin path, which shouldn't be public). Ask for a copy if you need it. Backend
only so far — see "Status" below.

**Stack:** Python 3.12 + Django 5 + Django REST Framework, PostgreSQL 16, Redis 7, Celery.
No frontend yet (React SPA is Phase 2).

> The previous FastAPI/SQLite/Jinja2 version of this project lives on the `legacy-fastapi`
> branch for reference. It is not being extended further.

## Status

Implemented, with real Postgres migrations and a passing test suite:

- **accounts** — custom `User` model, session auth (`/api/v1/auth/register|login|logout|me`),
  role groups (`worker`/`manager`/`admin`) seeded from `apps/accounts/roles.py`.
- **catalog** — categories, products, variants (the SKU), full-text + trigram search,
  variant-matrix generation, barcode assignment. Public read API under `/api/v1/products`,
  `/api/v1/categories`.
- **inventory** — the append-only stock ledger (`record_movement`), reservations with TTL
  expiry, stocktakes, nightly ledger/cache reconciliation. This is the part of the spec
  marked "read before changing anything" — see `apps/inventory/services.py`.
- **audit** — append-only `AuditLog`, written explicitly from services (never via signals).
- **orders** — cart + checkout (reserve at checkout-start, commit on confirm), POS in-store
  sales (`create_pos_order`, immediate ledger decrement, VAT-inclusive tax, cash/card capture),
  and the full order status machine: fulfil → ship → deliver, cancel, and partial/full refund
  with optional restocking. Buyer-facing `/api/v1/me/orders` is scoped so one buyer can never
  fetch another's order (404, not 403). See `apps/orders/services.py`.

`pricing` and `customers` are still schema-only stubs (discount codes and buyer
addresses/profiles aren't wired up yet).

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
`/api/v1/categories`). There's also a break-glass Django admin, superuser-only, mounted at an
obscure path in `config/urls.py` — not a daily interface, and its exact path deliberately isn't
repeated here (that's the point of it being obscure).

Postgres and Redis are also reachable from the host on `localhost:5433` and `localhost:6380`
(shifted off their default ports to avoid clashing with any local install).

## Running tests

```powershell
docker compose run --rm web python -m pytest
docker compose run --rm web ruff check .
```

The highest-priority tests are in `apps/inventory/tests/test_ledger.py` — they include a
multi-threaded test proving concurrent reservations against a single unit of stock cannot
oversell. `apps/accounts/tests/test_permission_matrix.py` is the permission matrix — add a row
for every new endpoint. `apps/orders/tests/test_selectors.py` covers the buyer-order IDOR case.

## Project layout

```
backend/
  config/               settings (base/dev/prod), urls, celery.py
  apps/
    core/               base models, exceptions, pagination, permissions — no business logic
    accounts/            User, roles, sessions
    catalog/              Product, Variant, Category, search
    inventory/             the stock ledger — see services.py before touching this app
    orders/                cart, checkout, POS sales, fulfilment, refunds
    pricing/               schema stub (Discount) — not wired up yet
    customers/              schema stub (Address, CustomerProfile) — not wired up yet
    audit/               AuditLog + record()
  docker-compose.yml
  Dockerfile
  requirements/{base,dev,prod}.txt
```

Each app follows the same internal shape (`models.py` / `services.py` / `selectors.py` /
`api/` / `tasks.py` / `admin.py`). The one rule that keeps it from rotting into a ball of mud:
**apps talk to each other only through `services.py`/`selectors.py`, never by importing
another app's models directly.**

## What's next

- The React back-office (products, variant matrix, stock adjustments, barcode lookup,
  stocktake UI, order management) — "run the real shop on this before writing any storefront
  code." The backend APIs it needs already exist.
- Real payment integration (checkout currently marks orders paid immediately — there's no
  payment gateway yet, `payment_ref` is accepted as a placeholder).
- Discount codes (`pricing` app), buyer addresses/profiles (`customers` app).
- Reporting, low-stock automation, purchase orders, prerendering for SEO.
- Productization (multi-tenant seams, catalog API, per-tenant theming).
