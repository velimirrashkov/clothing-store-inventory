# Clothing Store — Inventory & Webshop

A modular-monolith rebuild of the clothing store's inventory/webshop system, following an
architecture spec kept locally as `architecture-spec.md` (gitignored — not pushed to GitHub,
since it documents internal security controls like rate limits, session config, and the
break-glass admin path, which shouldn't be public). Ask for a copy if you need it.

**Stack:** Python 3.12 + Django 5 + Django REST Framework, PostgreSQL 16, Redis 7, Celery —
plus a React 18 + TypeScript + Vite back-office SPA (`/app/*`). No public storefront yet.

> The previous FastAPI/SQLite/Jinja2 version of this project lives on the `legacy-fastapi`
> branch for reference. It is not being extended further.

## Status

**Backend** — implemented, with real Postgres migrations and a passing test suite:

- **accounts** — custom `User` model, session auth (`/api/v1/auth/register|login|logout|me`),
  role groups (`worker`/`manager`/`admin`) seeded from `apps/accounts/roles.py`.
- **catalog** — categories, products, variants (the SKU), full-text + trigram search,
  variant-matrix generation, barcode assignment. Public read API under `/api/v1/products`,
  `/api/v1/categories`, plus a back-office CRUD API under `/api/v1/admin/products`,
  `/api/v1/admin/variants`, `/api/v1/admin/categories`.
- **inventory** — the append-only stock ledger (`record_movement`), reservations with TTL
  expiry, stocktakes (with a list/detail API for the working UI), nightly ledger/cache
  reconciliation. This is the part of the spec marked "read before changing anything" —
  see `apps/inventory/services.py`.
- **audit** — append-only `AuditLog`, written explicitly from services (never via signals).
- **orders** — cart + checkout (reserve at checkout-start, commit on confirm), POS in-store
  sales (`create_pos_order`, immediate ledger decrement, VAT-inclusive tax, cash/card capture),
  and the full order status machine: fulfil → ship → deliver, cancel, and partial/full refund
  with optional restocking. Buyer-facing `/api/v1/me/orders` is scoped so one buyer can never
  fetch another's order (404, not 403). See `apps/orders/services.py`.

`pricing` and `customers` are still schema-only stubs (discount codes and buyer
addresses/profiles aren't wired up yet).

**Frontend** — a back-office SPA covering the spec's Phase 1 UI scope: products (lazy category
tree + master-detail editing), variant-matrix generation, per-variant stock adjustment, barcode
lookup (camera via `BarcodeDetector` where supported, manual entry everywhere else), stocktake
(open/count/close), and POS sell (cart → receipt). Verified end-to-end in a real browser against
the live API — see `frontend/src/`. No public storefront (Phase 2).

## Requirements

- Docker + Docker Compose (backend: Python 3.12, Postgres 16, Redis 7 — no local install needed)
- Node.js 18+ and npm (frontend dev server; the app itself only needs a browser once built)

## Setup

**Backend:**

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

**Frontend** (with the backend already running):

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the dev server proxies `/api` to the Django backend on
`:8000`, so requests stay same-origin from the browser's point of view (matches the production
same-origin design, cookies just work, no CORS needed). Sign in with the superuser (or any user
in the `worker`/`manager`/`admin` group) at `/app/login`.

## Running tests

```powershell
cd backend
docker compose run --rm web python -m pytest
docker compose run --rm web ruff check .

cd frontend
npm run build   # tsc type-check + production build
npm run lint
```

The highest-priority tests are in `apps/inventory/tests/test_ledger.py` — they include a
multi-threaded test proving concurrent reservations against a single unit of stock cannot
oversell. `apps/accounts/tests/test_permission_matrix.py` is the permission matrix — add a row
for every new endpoint. `apps/orders/tests/test_selectors.py` covers the buyer-order IDOR case.
`apps/catalog/tests/test_admin_api.py::test_admin_product_detail_reflects_real_stock` is a
regression test for a real bug caught while building the frontend: the admin product API
silently returned `available: 0` for every variant regardless of actual stock, because it never
computed real availability the way the public catalog endpoint does.

## Project layout

```
backend/
  config/               settings (base/dev/prod), urls, celery.py
  apps/
    core/               base models, exceptions, pagination, permissions — no business logic
    accounts/            User, roles, sessions
    catalog/              Product, Variant, Category, search, admin CRUD API
    inventory/             the stock ledger — see services.py before touching this app
    orders/                cart, checkout, POS sales, fulfilment, refunds
    pricing/               schema stub (Discount) — not wired up yet
    customers/              schema stub (Address, CustomerProfile) — not wired up yet
    audit/               AuditLog + record()
  docker-compose.yml
  Dockerfile
  requirements/{base,dev,prod}.txt

frontend/
  src/
    api/                 fetch client (session cookie + CSRF), hand-maintained types, React
                          Query hooks — one file per backend app (catalog.ts, inventory.ts, ...)
    auth/                login page, RequireAuth/RequirePermission route guards
    layout/               AppShell (nav + outlet)
    pages/
      products/            category tree + master-detail product editor + variant matrix
      inventory/            barcode lookup/scanner + low-stock view
      stocktake/            open/count/close
      sell/                 POS cart -> receipt
```

Each Django app follows the same internal shape (`models.py` / `services.py` / `selectors.py` /
`api/` / `tasks.py` / `admin.py`). The one rule that keeps it from rotting into a ball of mud:
**apps talk to each other only through `services.py`/`selectors.py`, never by importing
another app's models directly.**

The frontend's types (`frontend/src/api/types.ts`) are hand-maintained to mirror the DRF
serializers — the spec's long-term intent is a generated client from the OpenAPI schema at
`/api/schema/` (already wired up via drf-spectacular), which is a good follow-up once the API
surface stabilizes.

## What's next

- Real payment integration (checkout currently marks orders paid immediately — there's no
  payment gateway yet, `payment_ref` is accepted as a placeholder).
- Discount codes (`pricing` app), buyer addresses/profiles (`customers` app).
- The public storefront (Phase 2): browsing, cart, checkout as a buyer, order history.
- Reporting, low-stock automation, purchase orders, prerendering for SEO.
- Generate the frontend API client from the OpenAPI schema instead of hand-maintaining types.
- Productization (multi-tenant seams, catalog API, per-tenant theming).
