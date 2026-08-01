# Clothing Store — Inventory & Webshop
## Architecture, Database & Backend Specification

**Version:** 0.1 (draft)
**Scope:** Single physical store + online shop, shared stock pool, one warehouse/location.

---

## 1. Decisions locked in

| Area | Decision |
|---|---|
| Backend | Python 3.12 + Django 5.x + Django REST Framework |
| Database | PostgreSQL 16 |
| Cache / broker | Redis 7 |
| Async jobs | Celery + Celery Beat |
| Frontend | React 18 + TypeScript + Vite (SPA), **no Next.js** |
| Admin UI | Custom React back-office. Django admin kept **superuser-only, break-glass** |
| Search | Postgres full-text (phase 1) → Meilisearch if needed |
| Stock model | Append-only ledger, single shared pool across store + web |
| Auth | Session cookies (HttpOnly, Secure, SameSite) + CSRF, same-origin deploy |
| Payments/fiscal | Deferred — see §12 for the seams to leave open |

### Why no Next.js
No SSR means no Node runtime in production — one less service, one less attack surface, one less deploy target. The tradeoff is SEO: a pure SPA storefront is weaker for organic search. Mitigation in §11.

---

## 2. Module segregation

**Answer: multiple Django apps, one project. A modular monolith — not a single app, not microservices.**

A single app becomes a 4,000-line `models.py` within a year and every import is circular. Microservices would mean distributed transactions across catalog and inventory for a shop with one location — pure cost, no benefit.

### 2.1 Layout

```
backend/
  config/                  # settings, urls, wsgi, celery
    settings/
      base.py
      dev.py
      prod.py
  apps/
    accounts/              # User, roles, sessions, MFA
    catalog/               # Product, Variant, Category, Attribute, Media
    inventory/             # StockMovement, StockLevel, Reservation, StockCount
    orders/                # Cart, Order, OrderLine, Shipment, Return
    pricing/               # PriceList, Discount, Promotion
    customers/             # Customer profile, addresses
    audit/                 # AuditLog, generic recorder
    core/                  # base models, mixins, exceptions, pagination, permissions
  tests/
```

Each app has the same internal shape:

```
apps/inventory/
  models.py            # ORM only. No business logic beyond validation.
  services.py          # ALL business logic. Public function surface of the app.
  selectors.py         # Read queries. Nothing here writes.
  api/
    views.py           # Thin. Parse -> call service -> serialize.
    serializers.py     # I/O shape only. No business rules.
    urls.py
  tasks.py             # Celery tasks. Thin wrappers over services.
  events.py            # Domain signals emitted by this app
  admin.py             # Break-glass Django admin registration
  migrations/
  tests/
```

### 2.2 The rule that keeps it clean

**Apps talk to each other only through `services.py` and `selectors.py`. Never import another app's models directly, never query another app's tables.**

```python
# WRONG — orders reaching into inventory's tables
from apps.inventory.models import StockLevel
StockLevel.objects.filter(variant_id=v).update(quantity=F("quantity") - 1)

# RIGHT
from apps.inventory import services as inventory_services
inventory_services.reserve(variant_id=v, quantity=1, ref=order.reference)
```

Foreign keys across apps are fine (`OrderLine.variant → catalog.Variant`). Reaching into another app's *logic* is not.

### 2.3 Dependency direction

Dependencies flow one way. If you need an arrow to go backwards, emit a domain event instead.

```
core        <- everyone
accounts    <- everyone
catalog     <- inventory, orders, pricing
inventory   <- orders
pricing     <- orders
customers   <- orders
audit       <- everyone (write-only)
```

`inventory` must never import from `orders`. When an order is paid, `orders` calls `inventory_services.commit_reservation(...)`. When stock hits zero, `inventory` emits an event; `catalog` listens and flips availability.

### 2.4 When to split out a service

Only if one of these becomes true: a module needs independent scaling (it won't at this size), a module needs a different runtime, or a module is sold separately. Until then, the app boundary gives you 90% of the modularity at 5% of the cost — and because the boundaries are already enforced, extracting one later is mechanical.

---

## 3. System architecture

```
                    ┌──────────────────────────────┐
                    │  Caddy / Traefik (TLS, CSP)  │
                    └──────────────┬───────────────┘
                                   │  same origin
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
   /  (static)              /api/*  (DRF)              /media/* (CDN)
   React SPA bundle         Gunicorn + Django          object storage
        │                          │
        │                   ┌──────┴───────┐
        │                   │              │
        │              PostgreSQL       Redis
        │                                  │
        │                            Celery workers
        │                            Celery beat
        └── storefront routes (public)
        └── /app/* back-office routes (staff, code-split bundle)
```

**One React app, two route trees.** `/` is the storefront; `/app/*` is the back-office, lazy-loaded as a separate chunk so buyers never download it. Route guards read the session's permission set. This keeps a single build, a single deploy, a single design system.

Serving the SPA from the same origin as the API is deliberate: it lets you use session cookies instead of tokens in JavaScript storage, which removes the entire XSS-to-account-takeover path. Do not split onto `app.example.com` + `api.example.com` unless you have a strong reason.

---

## 4. Data model

### 4.1 Conventions

- Primary keys: `BIGSERIAL` internally; expose **UUID or slug** in URLs for public-facing objects (never leak sequential order counts).
- Timestamps: `created_at`, `updated_at`, `timestamptz`, UTC only.
- Money: `BIGINT` minor units + `currency CHAR(3)`. **No floats, no `DECIMAL` guesswork.**
- Soft delete only where genuinely needed (`archived_at` on products). Orders are never deleted.
- Every table that a human can modify gets an audit trail entry (§8.5).

### 4.2 accounts

```sql
users
  id                BIGSERIAL PK
  public_id         UUID UNIQUE DEFAULT gen_random_uuid()
  email             CITEXT UNIQUE NOT NULL
  password          VARCHAR(128) NOT NULL          -- Argon2
  first_name        VARCHAR(150)
  last_name         VARCHAR(150)
  is_active         BOOLEAN NOT NULL DEFAULT TRUE
  is_staff          BOOLEAN NOT NULL DEFAULT FALSE -- back-office access at all
  is_superuser      BOOLEAN NOT NULL DEFAULT FALSE
  email_verified_at TIMESTAMPTZ NULL
  mfa_enabled       BOOLEAN NOT NULL DEFAULT FALSE
  last_login_at     TIMESTAMPTZ NULL
  created_at, updated_at
```

Use Django's built-in `Group` and `Permission` tables — do not reinvent them. Groups are your roles:

| Group | Grants |
|---|---|
| `buyer` | implicit; any authenticated non-staff user |
| `worker` | `catalog.view_*`, `inventory.adjust_stock`, `inventory.run_count`, `orders.fulfil_order` |
| `manager` | worker + `pricing.*`, `catalog.change_*`, `orders.refund_order`, `reports.view_*` |
| `admin` | manager + `accounts.manage_users`, `accounts.assign_roles` |

Custom permissions are declared in each app's `Meta.permissions`. **Always check permissions, never group names.**

```
totp_devices        -- django-otp
login_attempts      -- django-axes (or your own): ip, email, success, at
sessions            -- Django's session table, backed by Redis or DB
```

### 4.3 catalog

```sql
categories
  id PK, parent_id FK->categories NULL, name, slug UNIQUE, position INT, is_active

products
  id PK
  public_id     UUID UNIQUE
  slug          VARCHAR UNIQUE NOT NULL
  name          VARCHAR(255) NOT NULL
  description   TEXT
  category_id   FK->categories
  brand         VARCHAR(120) NULL
  gender        VARCHAR(20)         -- men | women | unisex | kids
  season        VARCHAR(20) NULL
  status        VARCHAR(20)         -- draft | active | archived
  created_at, updated_at, archived_at NULL

variants                            -- THE stock-keeping unit
  id PK
  public_id     UUID UNIQUE
  product_id    FK->products ON DELETE RESTRICT
  sku           VARCHAR(64) UNIQUE NOT NULL
  barcode       VARCHAR(32) UNIQUE NULL      -- EAN-13
  size          VARCHAR(20) NOT NULL         -- S, M, L, 38, 40...
  color         VARCHAR(40) NOT NULL
  color_hex     CHAR(7) NULL
  price_amount  BIGINT NOT NULL              -- minor units
  currency      CHAR(3) NOT NULL DEFAULT 'EUR'
  compare_at_amount BIGINT NULL              -- strike-through price
  weight_grams  INT NULL
  is_active     BOOLEAN NOT NULL DEFAULT TRUE
  created_at, updated_at
  UNIQUE (product_id, size, color)

product_media
  id PK, product_id FK, variant_id FK NULL, url, alt_text, position INT, is_primary BOOL
```

Indexes: `variants(sku)`, `variants(barcode)`, `variants(product_id)`, `products(status, category_id)`, GIN index on a `search_vector tsvector` column over name + description + brand.

> **Design note.** Size and color are explicit columns rather than a generic EAV attribute system. For a clothing store this is the right call — it makes queries, filters, and the size matrix UI simple and fast. If you later sell products with genuinely different axes, add a nullable JSONB `attributes` column rather than rebuilding.

### 4.4 inventory

This is the heart of the system. Read §5 before changing anything here.

```sql
locations                            -- seeded with exactly one row for now
  id PK, code VARCHAR(20) UNIQUE, name, is_default BOOLEAN

stock_movements                      -- APPEND ONLY. Never UPDATE, never DELETE.
  id            BIGSERIAL PK
  variant_id    FK->variants ON DELETE RESTRICT
  location_id   FK->locations
  delta         INTEGER NOT NULL CHECK (delta <> 0)
  reason        VARCHAR(30) NOT NULL
  reference     VARCHAR(64) NULL      -- order ref, delivery note, count id
  note          TEXT NULL
  actor_id      FK->users NULL        -- NULL = system
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()

  -- reason ∈ receipt | sale_online | sale_pos | return | damage | loss
  --          | count_adjustment | correction | initial_load

stock_levels                          -- denormalized cache of the ledger
  variant_id    FK->variants PK
  location_id   FK->locations
  on_hand       INTEGER NOT NULL DEFAULT 0
  reserved      INTEGER NOT NULL DEFAULT 0
  updated_at    TIMESTAMPTZ
  CHECK (on_hand >= 0)
  CHECK (reserved >= 0)
  CHECK (reserved <= on_hand)
  PRIMARY KEY (variant_id, location_id)

reservations
  id            BIGSERIAL PK
  variant_id    FK->variants
  location_id   FK->locations
  quantity      INTEGER NOT NULL CHECK (quantity > 0)
  order_id      FK->orders NULL
  cart_id       FK->carts NULL
  status        VARCHAR(20) NOT NULL   -- active | committed | released | expired
  expires_at    TIMESTAMPTZ NOT NULL
  created_at, updated_at
  INDEX (status, expires_at)
  INDEX (variant_id, status)

stock_counts                          -- physical stocktake sessions
  id PK, location_id FK, status (open|closed), started_by FK->users,
  started_at, closed_at

stock_count_lines
  id PK, count_id FK, variant_id FK, expected INT, counted INT NULL,
  counted_by FK->users NULL, counted_at NULL
  UNIQUE (count_id, variant_id)
```

**Available to sell = `on_hand - reserved`.** Never expose `on_hand` alone to the storefront.

`location_id` is present even though there is one location today. It costs nothing now and saves a brutal migration if you open a second shop or a separate warehouse.

### 4.5 pricing

```sql
discounts
  id PK, code VARCHAR(40) UNIQUE NULL, name, type (percent|fixed|free_shipping),
  value INT, min_order_amount BIGINT NULL, starts_at, ends_at,
  max_uses INT NULL, used_count INT DEFAULT 0, is_active BOOL

discount_targets                     -- optional scoping
  id PK, discount_id FK, product_id FK NULL, category_id FK NULL
```

Variant-level sale pricing lives in `variants.compare_at_amount`. Keep price history in the audit log rather than a separate price table until you actually need scheduled price changes.

### 4.6 customers

```sql
customer_profiles
  id PK, user_id FK->users UNIQUE, phone VARCHAR(32) NULL,
  marketing_opt_in BOOL DEFAULT FALSE, opt_in_at TIMESTAMPTZ NULL,
  anonymized_at TIMESTAMPTZ NULL

addresses
  id PK, user_id FK, label, recipient_name, phone, line1, line2 NULL,
  city, postcode, country CHAR(2), is_default_shipping BOOL, is_default_billing BOOL
```

### 4.7 orders

```sql
carts
  id PK, public_id UUID UNIQUE, user_id FK NULL, session_key VARCHAR NULL,
  status (active|converted|abandoned), created_at, updated_at, expires_at

cart_lines
  id PK, cart_id FK, variant_id FK, quantity INT CHECK (quantity > 0),
  unit_amount BIGINT, added_at
  UNIQUE (cart_id, variant_id)

orders
  id            BIGSERIAL PK
  public_id     UUID UNIQUE
  reference     VARCHAR(20) UNIQUE NOT NULL   -- human-facing, e.g. ORD-2026-00417
  user_id       FK->users NULL                -- NULL allowed for guest checkout
  email         CITEXT NOT NULL
  channel       VARCHAR(10) NOT NULL          -- online | pos
  status        VARCHAR(20) NOT NULL
  payment_status VARCHAR(20) NOT NULL         -- pending | paid | refunded | failed
  subtotal_amount   BIGINT NOT NULL
  discount_amount   BIGINT NOT NULL DEFAULT 0
  shipping_amount   BIGINT NOT NULL DEFAULT 0
  tax_amount        BIGINT NOT NULL DEFAULT 0
  total_amount      BIGINT NOT NULL
  currency          CHAR(3) NOT NULL
  discount_id   FK->discounts NULL
  shipping_address  JSONB NOT NULL            -- frozen snapshot, not a FK
  billing_address   JSONB NULL
  placed_at, updated_at
  INDEX (user_id, placed_at DESC), INDEX (status), INDEX (reference)

order_lines
  id PK, order_id FK, variant_id FK ON DELETE RESTRICT,
  sku VARCHAR(64) NOT NULL,          -- frozen
  product_name VARCHAR(255) NOT NULL, -- frozen
  size VARCHAR(20), color VARCHAR(40),-- frozen
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_amount BIGINT NOT NULL,        -- frozen
  line_total BIGINT NOT NULL

shipments
  id PK, order_id FK, carrier VARCHAR(40), tracking_number VARCHAR(80) NULL,
  status (pending|shipped|delivered|returned), shipped_at NULL, delivered_at NULL

returns
  id PK, order_id FK, status (requested|approved|received|refunded|rejected),
  reason TEXT, requested_at, resolved_at NULL

return_lines
  id PK, return_id FK, order_line_id FK, quantity INT, restock BOOLEAN
```

**Freeze everything on the order line.** Product name, SKU, size, colour, and price are copied at purchase time. If someone renames a product or changes a price two years later, the invoice must not change. This is both an accounting requirement and a customer-trust one.

`channel = pos` covers in-store sales entering the same ledger — that's how the shared pool actually stays correct.

### 4.8 audit

```sql
audit_log                             -- append only
  id BIGSERIAL PK
  actor_id      FK->users NULL
  actor_email   CITEXT NULL           -- frozen, survives user deletion
  action        VARCHAR(60) NOT NULL  -- stock.adjust, price.change, role.assign...
  object_type   VARCHAR(60) NOT NULL
  object_id     VARCHAR(64) NOT NULL
  changes       JSONB NULL            -- {"field": {"from": x, "to": y}}
  ip_address    INET NULL
  user_agent    TEXT NULL
  created_at    TIMESTAMPTZ DEFAULT now()
  INDEX (object_type, object_id, created_at DESC)
  INDEX (actor_id, created_at DESC)
```

Revoke UPDATE and DELETE on this table from the application DB role. It is evidence, not data.

---

## 5. Inventory mechanics

### 5.1 The ledger is the truth

`stock_levels` is a cache. It exists because summing millions of movement rows on every product page is absurd. But if the two ever disagree, **the ledger wins** and the cache is rebuilt:

```sql
SELECT variant_id, location_id, SUM(delta)
FROM stock_movements GROUP BY variant_id, location_id;
```

Run this as a nightly reconciliation job and alert on any mismatch. A mismatch means a bug, and you want to find it in week two, not after inventory has drifted for a year.

### 5.2 Every write is a movement

There is exactly one way stock changes: `inventory_services.record_movement()`. No view, no task, no admin action ever does `stock_level.on_hand = X`. This single rule is what makes the audit trail trustworthy.

```python
@transaction.atomic
def record_movement(*, variant_id, delta, reason, actor=None,
                    reference=None, note=None, location_id=None):
    location_id = location_id or default_location_id()

    level = (StockLevel.objects
             .select_for_update()
             .get_or_create(variant_id=variant_id, location_id=location_id)[0])

    new_on_hand = level.on_hand + delta
    if new_on_hand < 0:
        raise InsufficientStock(variant_id=variant_id,
                                requested=abs(delta), available=level.on_hand)
    if new_on_hand < level.reserved:
        raise ReservedStockConflict(...)

    movement = StockMovement.objects.create(
        variant_id=variant_id, location_id=location_id, delta=delta,
        reason=reason, reference=reference, note=note, actor=actor)

    level.on_hand = new_on_hand
    level.save(update_fields=["on_hand", "updated_at"])

    audit.record(actor=actor, action=f"stock.{reason}",
                 object_type="variant", object_id=variant_id,
                 changes={"on_hand": {"from": level.on_hand - delta,
                                      "to": new_on_hand}})
    return movement
```

`select_for_update()` is not optional. It is the lock that stops two concurrent checkouts from both selling the last item. The row-level `CHECK (on_hand >= 0)` constraint is the backstop for the day someone forgets.

### 5.3 Reservation lifecycle

```
  add to cart          checkout starts        payment confirmed
       │                      │                       │
       ▼                      ▼                       ▼
  (no reservation)   reserve() ──────────────► commit()
                          │                       │
                          │                       ├─► movement(delta = -qty,
                          │                       │            reason = sale_online)
                          │                       └─► reservation.status = committed
                          │
                          ├─ user abandons ──► expire()  (Celery Beat, every 2 min)
                          └─ user cancels  ──► release()
```

- Reserve **at checkout start**, not at add-to-cart. Reserving in the cart means one indecisive shopper blocks stock for hours.
- `expires_at = now() + 20 minutes`. Long enough to complete a payment, short enough not to strand stock.
- `commit()` converts reservation → movement in a single transaction. The reservation row stays, marked `committed`, as an audit record.
- The expiry job must be idempotent and must lock rows — it will race with real checkouts.

### 5.4 In-store sales

A POS sale calls the same `record_movement(reason="sale_pos")`. Because both channels write to one ledger and read one `available` figure, the shared pool works with no reconciliation logic. The only real risk is a shop-floor sale that never gets entered — which is a process problem, solved by making the scanner app fast rather than by making the software cleverer.

### 5.5 Overselling policy

Even with locking, physical reality drifts (theft, damage, miscounts). Decide explicitly:

- **Strict** (recommended for launch): never accept an order that exceeds available. Buyers see "out of stock".
- **Buffer**: hold back N units per variant from the online available figure. Configurable per variant, protects the shop floor.
- **Backorder**: accept and flag. Only if you have reliable supplier lead times.

Implement strict; leave `variants.online_buffer INT DEFAULT 0` in the schema so switching is a config change.

### 5.6 Stocktake

Open a count → snapshot `expected` for every active variant → workers scan and enter `counted` → close the count, which generates one `count_adjustment` movement per discrepancy with the count ID as `reference`. Never overwrite levels directly from a count.

---

## 6. Authentication & authorization

### 6.1 Session auth for the SPA

Same-origin deployment means standard Django session cookies work, which is both simpler and safer than tokens.

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14      # buyers
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False                 # SPA must read it to echo the header
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
```

React reads the `csrftoken` cookie and sends it as `X-CSRFToken` on every mutating request. Set `withCredentials: true` on the HTTP client. Staff sessions get a shorter age (8 hours) and an idle timeout.

Do **not** put JWTs in `localStorage`. If you later need a mobile app or third-party API access, add scoped API tokens for that specific case — don't convert the web app.

### 6.2 Permission enforcement, three layers

**Layer 1 — endpoint permission.**

```python
class StockAdjustView(APIView):
    permission_classes = [IsAuthenticated, HasPerm("inventory.adjust_stock")]
```

**Layer 2 — object ownership.** This is where real breaches happen. A buyer requesting `/api/orders/{public_id}/` must be checked against ownership, not merely against "is a buyer".

```python
def get_order_for_user(*, public_id, user):
    qs = Order.objects.filter(public_id=public_id)
    if not user.has_perm("orders.view_any_order"):
        qs = qs.filter(user=user)
    return qs.get()          # raises DoesNotExist -> 404, never 403
```

Return **404, not 403**, for objects a user may not see. A 403 confirms the object exists.

**Layer 3 — field-level.** Serializers differ by role. A worker fetching a variant sees stock; a buyer sees only `in_stock: true|false`. Use separate serializer classes, not conditional field stripping — conditionals leak.

### 6.3 Role matrix

| Capability | buyer | worker | manager | admin |
|---|:--:|:--:|:--:|:--:|
| Browse catalog, place order | ✔ | ✔ | ✔ | ✔ |
| View own orders | ✔ | ✔ | ✔ | ✔ |
| View all orders | | ✔ | ✔ | ✔ |
| Exact stock figures | | ✔ | ✔ | ✔ |
| Adjust stock / run counts | | ✔ | ✔ | ✔ |
| Fulfil, ship orders | | ✔ | ✔ | ✔ |
| Create / edit products | | | ✔ | ✔ |
| Change prices, discounts | | | ✔ | ✔ |
| Issue refunds | | | ✔ | ✔ |
| Reports | | | ✔ | ✔ |
| Manage users & roles | | | | ✔ |

This table is also the test fixture — see §10.2.

### 6.4 Account security

- Argon2 hashing (`PASSWORD_HASHERS` with `Argon2PasswordHasher` first).
- Mandatory TOTP MFA for anyone with `is_staff`; optional for buyers.
- Rate limits: login 5/min/IP and 10/hour/account; password reset 3/hour/email; registration 10/hour/IP.
- Email verification before first order.
- Generic error text on login — never reveal whether the email exists.
- Password reset tokens: single-use, 1-hour expiry, invalidate all sessions on reset.
- Session invalidation on password change and on role change.
- Separate login route for staff (`/app/login`) — different rate limits and mandatory MFA.

---

## 7. API design

### 7.1 Conventions

- Base path `/api/v1/`. Version from day one; it costs nothing now.
- snake_case JSON. Cursor pagination on anything unbounded.
- Public identifiers in URLs are UUIDs or slugs, never integer PKs.
- Errors are uniform:

```json
{
  "error": {
    "code": "insufficient_stock",
    "message": "Only 2 items available",
    "details": {"variant_id": "…", "available": 2, "requested": 5}
  }
}
```

- Idempotency: `POST /orders` accepts an `Idempotency-Key` header. Double-clicked checkout must not create two orders.

### 7.2 Endpoint surface

**Public / storefront**
```
GET    /api/v1/products                    ?category=&size=&color=&q=&sort=&cursor=
GET    /api/v1/products/{slug}             includes variants + availability booleans
GET    /api/v1/categories
POST   /api/v1/cart                        create or fetch current cart
GET    /api/v1/cart
POST   /api/v1/cart/lines
PATCH  /api/v1/cart/lines/{id}
DELETE /api/v1/cart/lines/{id}
POST   /api/v1/checkout/start              -> creates reservations, returns expiry
POST   /api/v1/checkout/confirm            -> creates order, commits reservations
```

**Buyer account**
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me                     -> {user, permissions[]}
POST   /api/v1/auth/password-reset
GET    /api/v1/me/orders
GET    /api/v1/me/orders/{public_id}
CRUD   /api/v1/me/addresses
POST   /api/v1/me/returns
DELETE /api/v1/me                          -> GDPR anonymization request
```

**Back-office** (all under `/api/v1/admin/`, all permission-gated)
```
CRUD   /products                           incl. bulk variant matrix creation
POST   /products/{id}/media
CRUD   /variants
GET    /inventory/levels                   ?low_stock=true&q=
POST   /inventory/movements                {variant_id, delta, reason, note}
POST   /inventory/lookup                   {barcode} -> variant + level
POST   /inventory/counts                   open a stocktake
POST   /inventory/counts/{id}/lines
POST   /inventory/counts/{id}/close
GET    /orders                             ?status=&channel=&from=&to=
GET    /orders/{public_id}
POST   /orders/{public_id}/fulfil
POST   /orders/{public_id}/ship
POST   /orders/{public_id}/refund
POST   /orders/pos                         in-store sale entry
CRUD   /discounts
GET    /reports/sales                      ?granularity=day|week|month
GET    /reports/stock-value
GET    /reports/slow-movers
CRUD   /users                              admin only
POST   /users/{id}/roles                   admin only
GET    /audit                              ?object_type=&object_id=&actor=
```

### 7.3 The `/auth/me` contract

The SPA needs the permission list to render navigation and guard routes:

```json
{
  "user": {"public_id": "…", "email": "…", "first_name": "…", "is_staff": true},
  "permissions": ["catalog.view_product", "inventory.adjust_stock", "orders.fulfil_order"]
}
```

Frontend guards are **UX, not security**. Every endpoint re-checks server-side. Assume a hostile client at all times.

---

## 8. Backend functionality by module

### 8.1 catalog

- `create_product`, `update_product`, `archive_product` (archive never deletes — order lines reference variants).
- `generate_variant_matrix(product, sizes[], colors[], base_price)` — creates the full size × colour grid in one call, auto-generating SKUs (`{PRODUCT}-{COLOR}-{SIZE}`). This one function saves hours of data entry per season.
- `assign_barcodes(variant_ids)` — EAN-13 with checksum.
- Media upload → Celery task generates 400w/800w/1600w WebP derivatives, writes to object storage, updates `product_media`.
- `search_products(query, filters)` — Postgres `tsvector` with a trigram fallback for typos.
- Availability is **derived**, never stored on the product: `available = on_hand - reserved > 0` via `inventory.selectors`.

### 8.2 inventory

Public service surface (nothing else touches stock):

```python
record_movement(variant_id, delta, reason, actor, reference, note)
receive_stock(lines[], reference, actor)          # bulk delivery intake
reserve(variant_id, quantity, cart_id, ttl)       -> Reservation
release(reservation_id)
commit_reservation(reservation_id, order_ref)
expire_stale_reservations()                       # Celery Beat, every 2 min
get_available(variant_id)                         -> int
bulk_availability(variant_ids[])                  -> dict   # avoids N+1
open_count(location, actor) / submit_count_line() / close_count()
reconcile_levels()                                # nightly, ledger vs cache
low_stock_variants(threshold)
```

Emits: `stock_depleted`, `stock_replenished`, `low_stock_reached`.

### 8.3 orders

```python
get_or_create_cart(user, session_key)
add_line(cart, variant_id, quantity)              # validates availability, no reserve
start_checkout(cart)                              # reserves all lines atomically
confirm_order(cart, addresses, payment_ref)       # creates order, commits reservations
cancel_order(order, actor, reason)                # releases or reverses stock
fulfil_order(order, actor)
ship_order(order, carrier, tracking)
refund_order(order, lines[], restock: bool, actor)
create_pos_order(lines[], actor)                  # in-store, immediate sale movement
```

Order status machine — enforce transitions in the service, never allow arbitrary status writes:

```
pending_payment ─► paid ─► processing ─► shipped ─► delivered
       │             │          │
       └─► cancelled ◄┴──────────┘
                     └─► refunded (partial or full)
```

`start_checkout` must reserve **all** lines or none — one transaction, and sort variant IDs before locking to avoid deadlocks between concurrent checkouts.

### 8.4 pricing

`calculate_cart_total(cart, discount_code)` returns a full breakdown (subtotal, discount, shipping, tax, total). It is a pure function of its inputs and the single source of truth for totals — the frontend displays what it returns and never computes money itself. Validate the discount again at `confirm_order`; the code may have expired between page load and submit.

### 8.5 audit

```python
audit.record(actor, action, object_type, object_id, changes, request=None)
```

Called explicitly from services rather than via signals — signals make it too easy to lose the actor and the intent. Mandatory for: any stock movement, price change, role assignment, refund, user deactivation, order cancellation.

### 8.6 Background jobs

| Job | Schedule | Purpose |
|---|---|---|
| `expire_stale_reservations` | every 2 min | release abandoned checkouts |
| `reconcile_stock_levels` | nightly 03:00 | ledger vs cache, alert on drift |
| `low_stock_report` | daily 08:00 | email variants below threshold |
| `abandoned_cart_cleanup` | daily | mark carts stale after 7 days |
| `generate_image_derivatives` | on upload | WebP resizing |
| `send_transactional_email` | on demand | order confirmation, shipping notice |
| `rebuild_search_vectors` | on product save | full-text index |
| `db_backup_verify` | daily | restore last dump into a scratch DB |

---

## 9. Frontend notes

- **Vite + React 18 + TypeScript**, strict mode on.
- **TanStack Query** for all server state. No Redux — you have almost no client state that isn't server state.
- **Types generated from the API**, not hand-written: emit an OpenAPI schema with `drf-spectacular` and generate a typed client in CI. Hand-maintained interfaces drift within weeks and silently lie to you.
- Routing: `react-router` with a `<RequirePermission perm="inventory.adjust_stock">` wrapper reading from the `/auth/me` cache.
- Back-office bundle lazy-loaded at `/app/*`. Buyers never fetch it.
- The scanner view is just a back-office route using `BarcodeDetector` or `zxing-js` on a phone browser — no native app needed for phase 1.
- UI kit: Tailwind + shadcn/ui, or Mantine if you want batteries included. Either beats fighting Django admin's CSS.

**Break-glass Django admin:** keep it mounted at an obscure path, superuser + MFA only, IP-restricted if practical. It is your recovery tool when the React app has a bug at 22:00 on a Friday — not a daily interface.

---

## 10. Testing strategy

Priority is blast radius, not coverage percentage.

### 10.1 Inventory invariants — highest priority

```python
def test_concurrent_checkout_cannot_oversell(transactional_db):
    variant = VariantFactory(); set_stock(variant, 1)
    results = run_in_threads(lambda: start_checkout_for(variant, qty=1), n=10)
    assert sum(r.success for r in results) == 1
    assert get_available(variant.id) == 0
```

Plus Hypothesis property tests: for any random sequence of movements, reservations, commits and releases — `on_hand == sum(deltas)`, `on_hand >= 0`, `reserved <= on_hand`.

### 10.2 Permission matrix — a security control, not a formality

```python
@pytest.mark.parametrize("role,method,endpoint,expected", PERMISSION_MATRIX)
def test_endpoint_permissions(client, role, method, endpoint, expected):
    login_as(client, role)
    assert getattr(client, method)(endpoint).status_code == expected
```

`PERMISSION_MATRIX` is generated from §6.3. Add a row for every new endpoint — make it a PR checklist item. Include the IDOR cases: buyer A requesting buyer B's order must get 404.

### 10.3 The rest

- Service-layer unit tests with `factory_boy`. Business logic lives outside views precisely so it's testable without HTTP.
- Contract tests: Schemathesis against the OpenAPI schema catches serializer drift automatically.
- E2E in Playwright: browse → cart → checkout → order visible in back-office → fulfil → stock decremented. That single path covers most of the system.
- Migration tests: apply all migrations against a copy of production-shaped data in CI.
- Load test with Locust before any sale event — concurrent checkout on a small set of variants is the realistic worst case.

Target: ~85% on `services.py` and `selectors.py`, and don't chase coverage in serializers or admin.

---

## 11. Deployment

Single Hetzner VPS (EU, low latency to BG), Docker Compose:

```
caddy        TLS, static SPA, reverse proxy, security headers
web          gunicorn + django  (2–4 workers)
worker       celery
beat         celery beat
postgres     16, volume-mounted
redis        7
```

- CI (GitHub Actions): lint (ruff) → type check (mypy) → tests → build image → push → deploy → migrate. Tests gate the build.
- Migrations run as a separate step before the new container takes traffic. Backwards-compatible migrations only (add column → deploy → backfill → drop old column).
- Backups: `pg_dump` nightly to offsite object storage + WAL archiving. **A restore is tested weekly by an automated job.** An untested backup is a hope.
- Sentry for errors, `/healthz` endpoint, uptime monitor, structured JSON logs.
- Staging with anonymized production data. Never point tests at production.

**SEO for the SPA storefront:** server-render only the product and category pages via a small prerender step in CI, or add a prerender service for crawler user agents. Do this in phase 2, not phase 1 — but leave clean, crawlable URLs and real `<a href>` links from day one so it's a rendering change and not a rewrite.

---

## 12. Seams left for payments and fiscal compliance

Payments are deferred, but the schema should not have to change when they arrive:

- `orders.payment_status` exists and is separate from `orders.status`. Payment is not the same thing as fulfilment.
- Add a `payments` table when you integrate — `order_id`, `provider`, `provider_ref`, `amount`, `status`, `raw_payload JSONB`. Don't invent it now.
- `confirm_order` already takes a `payment_ref` argument. Today it's a placeholder; later it's the provider transaction ID.
- Never store card data. When the time comes, use a hosted/redirect checkout so PCI scope stays at SAQ-A.
- Fiscal receipt generation, if required, hooks onto the `order.paid` event — keep that event emitted from day one even though nothing listens yet.
- Currency is already a column on every money-carrying table, so a display-layer change covers dual-currency presentation without a migration.

---

## 13. Build order

**Phase 1 — Inventory core (4–6 weeks).** accounts, catalog, inventory, audit. Back-office React app: products, variant matrix, stock adjustments, barcode lookup, stocktake. POS order entry. **Run the real shop on this before writing any storefront code.** If it can't replace the current process, nothing downstream matters.

**Phase 2 — Storefront.** Public catalog, cart, checkout with reservations, buyer accounts, order history, transactional email. Payments integrated here.

**Phase 3 — Operations.** Returns, refunds, reporting, low-stock automation, supplier purchase orders, prerendering for SEO.

**Phase 4 — Productization.** Multi-tenant seams, catalog API for the chatbot to consume as its retrieval source, per-tenant theming. This is where the internal tool becomes something you can sell.

---

## 14. Rules that keep this maintainable

1. Business logic lives in `services.py`. Views parse and serialize; models validate. Nothing else.
2. Apps communicate through services and selectors only — never across each other's models.
3. Stock changes exclusively through `record_movement()`. No exceptions, ever.
4. Money is integer minor units. Never a float.
5. Order lines freeze their data at purchase time.
6. Every permission check happens server-side. Frontend guards are cosmetic.
7. `select_for_update()` on every stock write.
8. Public URLs expose UUIDs, never sequential IDs.
9. The audit log is append-only at the database privilege level.
10. Every new endpoint adds a row to the permission matrix test.
