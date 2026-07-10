"""One-off script to populate the dev database with realistic sample data.

Run with: .\\venv\\Scripts\\python.exe seed_data.py
Safe to re-run against an empty database; not idempotent against a populated one.
"""
import datetime
import random

from app.database import Base, SessionLocal, engine
from app import models
from app.routers.sales import consume_fifo

random.seed(42)

SIZES = models.STANDARD_SIZES
COLORS = [
    "Black", "White", "Navy", "Grey", "Beige", "Olive",
    "Burgundy", "Denim Blue", "Charcoal", "Cream",
]
MATERIALS = [
    "100% Cotton", "95% Cotton, 5% Elastane", "80% Cotton, 20% Polyester",
    "100% Polyester", "60% Cotton, 40% Polyester", "100% Linen",
    "98% Cotton, 2% Elastane", "70% Viscose, 30% Polyester",
]
CARE = [
    "Machine wash 30°C, do not bleach", "Hand wash cold, lay flat to dry",
    "Machine wash 40°C, tumble dry low", "Dry clean only",
    "Machine wash 30°C, iron low heat",
]
SEASONS = ["SS26", "FW25", "AW25", "SS25"]

SUPPLIER_NAMES = [
    "Acme Textiles", "Global Apparel Co", "Sofia Garment Works",
    "Balkan Textile Group", "EuroFashion Supply", "Textile Partners Ltd",
    "Nordic Knitwear", "Plovdiv Fabric House",
]

CATEGORY_TREE = {
    "Men": None,
    "Women": None,
    "Unisex": None,
    "Shirts (M)": "Men",
    "T-Shirts (M)": "Men",
    "Jeans (M)": "Men",
    "Jackets (M)": "Men",
    "Pants (M)": "Men",
    "Dresses": "Women",
    "Blouses": "Women",
    "Skirts": "Women",
    "Jackets (W)": "Women",
    "Jeans (W)": "Women",
    "Hoodies": "Unisex",
    "Accessories": None,
}

PRODUCT_TEMPLATES = {
    "Shirts (M)": ("Men", 30, 65, ["Classic Oxford Shirt", "Slim Fit Dress Shirt", "Flannel Check Shirt", "Linen Summer Shirt", "Striped Poplin Shirt"]),
    "T-Shirts (M)": ("Men", 15, 35, ["Basic Crew Neck Tee", "Graphic Print Tee", "V-Neck Cotton Tee", "Long Sleeve Tee", "Pocket Tee"]),
    "Jeans (M)": ("Men", 40, 90, ["Slim Fit Jeans", "Straight Leg Jeans", "Relaxed Fit Jeans", "Skinny Jeans", "Bootcut Jeans"]),
    "Jackets (M)": ("Men", 60, 150, ["Denim Jacket", "Bomber Jacket", "Puffer Jacket", "Leather Biker Jacket", "Windbreaker"]),
    "Pants (M)": ("Men", 35, 75, ["Chino Pants", "Cargo Pants", "Tailored Trousers", "Jogger Pants", "Corduroy Pants"]),
    "Dresses": ("Women", 40, 120, ["Floral Midi Dress", "Wrap Dress", "Shirt Dress", "Slip Dress", "A-Line Dress", "Bodycon Dress"]),
    "Blouses": ("Women", 25, 60, ["Silk Blouse", "Ruffle Blouse", "Sleeveless Blouse", "Printed Blouse"]),
    "Skirts": ("Women", 30, 70, ["Pleated Midi Skirt", "Denim Skirt", "Pencil Skirt", "Wrap Skirt"]),
    "Jackets (W)": ("Women", 55, 140, ["Cropped Denim Jacket", "Blazer Jacket", "Quilted Jacket", "Faux Leather Jacket"]),
    "Jeans (W)": ("Women", 40, 90, ["High-Waist Jeans", "Mom Jeans", "Skinny Jeans", "Flare Jeans"]),
    "Hoodies": ("Unisex", 30, 70, ["Classic Hoodie", "Zip-Up Hoodie", "Oversized Hoodie", "Cropped Hoodie"]),
    "Accessories": ("Unisex", 10, 40, ["Cotton Beanie", "Wool Scarf", "Canvas Tote Bag", "Leather Belt"]),
}

ADJECTIVES = ["Classic", "Modern", "Essential", "Premium", "Everyday", "Signature", "Urban", "Heritage"]

TARGET_PRODUCTS = 150
NUM_SUPPLIERS = 8
NUM_DELIVERIES = 8
NUM_SALES = 8


def utc_days_ago(days, hours=0):
    return datetime.datetime.utcnow() - datetime.timedelta(days=days, hours=hours)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(models.Product).count()
    if existing:
        print(f"Database already has {existing} products — aborting to avoid duplicating data.")
        return

    # --- Categories ---
    category_objs = {}
    for name, parent_name in CATEGORY_TREE.items():
        parent = category_objs.get(parent_name) if parent_name else None
        cat = models.Category(name=name, parent_id=parent.id if parent else None)
        db.add(cat)
        db.flush()
        category_objs[name] = cat
    print(f"Created {len(category_objs)} categories")

    # --- Suppliers ---
    suppliers = []
    for i, name in enumerate(SUPPLIER_NAMES[:NUM_SUPPLIERS]):
        s = models.Supplier(
            name=name,
            contact_name=f"Contact {i + 1}",
            phone=f"+359 88 {100000 + i * 111}",
            email=f"sales@{name.lower().replace(' ', '')}.com",
            address=f"{10 + i} Industrial Blvd, Sofia",
            notes="",
        )
        db.add(s)
        suppliers.append(s)
    db.flush()
    print(f"Created {len(suppliers)} suppliers")

    # --- Products + Variants ---
    products = []
    all_variants = []
    style_counter = 1

    leaf_categories = list(PRODUCT_TEMPLATES.keys())

    while len(products) < TARGET_PRODUCTS:
        for cat_name in leaf_categories:
            if len(products) >= TARGET_PRODUCTS:
                break
            gender, price_lo, price_hi, names = PRODUCT_TEMPLATES[cat_name]
            base_name = random.choice(names)
            adjective = random.choice(ADJECTIVES)
            full_name = f"{adjective} {base_name}"
            style_code = f"STY-{style_counter:04d}"
            style_counter += 1

            product = models.Product(
                name=full_name,
                style_code=style_code,
                gender=gender,
                category_id=category_objs[cat_name].id,
                sell_price=round(random.uniform(price_lo, price_hi), 2),
                description="",
                material_composition=random.choice(MATERIALS),
                care_instructions=random.choice(CARE),
                season=random.choice(SEASONS),
                status="active",
            )
            db.add(product)
            db.flush()
            products.append(product)

            sizes = random.sample(SIZES, k=random.randint(2, 3))
            colors = random.sample(COLORS, k=random.randint(1, 2))
            for size in sizes:
                for color in colors:
                    qty = 0 if random.random() < 0.12 else random.randint(1, 30)
                    sku = f"{style_code}-{size}-{color[:3].upper().replace(' ', '')}"
                    variant = models.Variant(
                        product_id=product.id,
                        size=size,
                        color_name=color,
                        sku=sku,
                        quantity=qty,
                    )
                    db.add(variant)
                    db.flush()
                    if qty:
                        db.add(models.StockMovement(
                            variant_id=variant.id, change=qty, reason="initial_stock",
                        ))
                    all_variants.append(variant)

            # link 1-2 suppliers per product
            for supplier in random.sample(suppliers, k=random.randint(1, 2)):
                cost = round(product.sell_price * random.uniform(0.35, 0.55), 2)
                db.add(models.ProductSupplier(
                    product_id=product.id,
                    supplier_id=supplier.id,
                    cost_price=cost,
                    supplier_sku=f"{supplier.name[:4].upper()}-{style_code}",
                ))

    db.commit()
    print(f"Created {len(products)} products with {len(all_variants)} variants")

    # --- Deliveries (Purchase Orders) ---
    delivery_variant_ids = set()
    po_statuses_cycle = ["received"] * 6 + ["ordered", "partial"]

    for i in range(NUM_DELIVERIES):
        supplier = random.choice(suppliers)
        links = (
            db.query(models.ProductSupplier)
            .filter(models.ProductSupplier.supplier_id == supplier.id)
            .all()
        )
        if not links:
            continue
        chosen_links = random.sample(links, k=min(len(links), random.randint(3, 6)))

        created_at = utc_days_ago(random.randint(10, 60))
        po = models.PurchaseOrder(
            supplier_id=supplier.id, status="draft", created_at=created_at,
            notes=f"Restock order #{i + 1}",
        )
        db.add(po)
        db.flush()

        status = po_statuses_cycle[i % len(po_statuses_cycle)]
        lines = []
        for link in chosen_links:
            variant = random.choice(
                [v for v in all_variants if v.product_id == link.product_id]
            )
            qty_ordered = random.randint(10, 40)
            line = models.PurchaseOrderLine(
                purchase_order_id=po.id,
                variant_id=variant.id,
                quantity_ordered=qty_ordered,
                unit_cost=link.cost_price,
            )
            db.add(line)
            db.flush()
            lines.append(line)
            delivery_variant_ids.add(variant.id)

        po.ordered_at = created_at + datetime.timedelta(days=1)
        if status in ("received", "partial"):
            po.status = "ordered"
            received_at = po.ordered_at + datetime.timedelta(days=random.randint(2, 7))
            for line in lines:
                receive_qty = line.quantity_ordered
                if status == "partial" and line is lines[-1]:
                    receive_qty = max(1, line.quantity_ordered // 2)
                db.add(models.StockBatch(
                    variant_id=line.variant_id,
                    purchase_order_line_id=line.id,
                    received_date=received_at,
                    quantity_received=receive_qty,
                    quantity_remaining=receive_qty,
                    buy_price=line.unit_cost,
                ))
                line.variant.quantity += receive_qty
                line.quantity_received = receive_qty
                db.add(models.StockMovement(
                    variant_id=line.variant_id, change=receive_qty, reason="received",
                    purchase_order_line_id=line.id,
                ))
            po.status = "received" if po.is_fully_received else "partial"
            po.received_at = received_at
        else:
            po.status = "ordered"

    db.commit()
    print(f"Created {NUM_DELIVERIES} purchase orders touching {len(delivery_variant_ids)} variants")

    # --- Sales (must not touch variants used in deliveries) ---
    available_pool = [v for v in all_variants if v.id not in delivery_variant_ids and v.quantity > 0]
    random.shuffle(available_pool)

    sales_created = 0
    pool_index = 0
    for i in range(NUM_SALES):
        num_lines = random.randint(1, 4)
        lines_data = []
        for _ in range(num_lines):
            if pool_index >= len(available_pool):
                break
            variant = available_pool[pool_index]
            pool_index += 1
            if variant.quantity <= 0:
                continue
            qty = min(variant.quantity, random.randint(1, 5))
            lines_data.append((variant, qty))

        if not lines_data:
            continue

        sale_time = utc_days_ago(random.randint(0, 29), hours=random.randint(0, 23))
        sale = models.Sale(timestamp=sale_time, total=0.0, note="")
        db.add(sale)
        db.flush()

        total = 0.0
        for variant, qty in lines_data:
            unit_price = variant.product.sell_price
            unit_cost = consume_fifo(db, variant, qty)
            sale_item = models.SaleItem(
                sale_id=sale.id, variant_id=variant.id, quantity=qty,
                unit_price=unit_price, unit_cost=unit_cost,
            )
            db.add(sale_item)
            db.flush()
            variant.quantity -= qty
            db.add(models.StockMovement(
                variant_id=variant.id, change=-qty, reason="sale",
                sale_item_id=sale_item.id,
            ))
            total += qty * unit_price

        sale.total = total
        sales_created += 1

    db.commit()
    print(f"Created {sales_created} sales")

    db.close()
    print("Done.")


if __name__ == "__main__":
    main()
