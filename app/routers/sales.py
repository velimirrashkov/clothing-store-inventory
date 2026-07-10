import json
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from ..i18n import get_lang, translator
from ..queries import build_category_tree
from ..templating import render

router = APIRouter()

SALES_PAGE_SIZE = 15
RECENT_SALES_LIMIT = 10


def consume_fifo(db: Session, variant: models.Variant, qty: int) -> float:
    """Consume `qty` units from the variant's stock batches oldest-first.

    Returns the quantity-weighted cost of the consumed units. Any quantity not
    covered by a batch (e.g. stock added without a purchase order) costs 0,
    matching the zero-cost-basis convention used elsewhere for non-purchased stock.
    """
    remaining = qty
    total_cost = 0.0
    batches = (
        db.query(models.StockBatch)
        .filter(models.StockBatch.variant_id == variant.id, models.StockBatch.quantity_remaining > 0)
        .order_by(models.StockBatch.received_date.asc(), models.StockBatch.id.asc())
        .all()
    )
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity_remaining, remaining)
        batch.quantity_remaining -= take
        total_cost += take * batch.buy_price
        remaining -= take
    return total_cost / qty if qty else 0.0


@router.get("/sell")
def sell_page(request: Request, db: Session = Depends(get_db)):
    variants = (
        db.query(models.Variant)
        .join(models.Product)
        .options(joinedload(models.Variant.product).joinedload(models.Product.category))
        .order_by(models.Product.name, models.Variant.size)
        .all()
    )

    recent_sales = (
        db.query(models.Sale)
        .order_by(models.Sale.timestamp.desc())
        .limit(RECENT_SALES_LIMIT)
        .all()
    )

    category_tree = build_category_tree(db)

    catalog = [
        {
            "variant_id": v.id,
            "label": f"{v.product.name} ({v.label})",
            "sku": v.sku,
            "price": v.product.sell_price,
            "stock": v.quantity,
            "category_id": v.product.category_id,
        }
        for v in variants
    ]

    t = translator(get_lang(request))
    js_strings = {
        "in_stock": t("sell.js_in_stock"),
        "remove": t("sell.js_remove"),
        "empty_cart_error": t("sell.js_empty_cart_error"),
        "no_items": t("sell.js_no_items"),
        "browse_hint": t("sell.js_browse_hint"),
        "uncategorized": t("sell.js_uncategorized"),
    }

    return render(
        request,
        "sales/sell.html",
        {
            "active": "sell",
            "catalog_json": json.dumps(catalog),
            "i18n_json": json.dumps(js_strings),
            "recent_sales": recent_sales,
            "category_tree_json": json.dumps(category_tree),
        },
    )


@router.post("/sell")
def complete_sale(
    variant_ids: list = Form([]),
    quantities: list = Form([]),
    unit_prices: list = Form([]),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    lines = []
    for variant_id_raw, qty_raw, price_raw in zip(variant_ids, quantities, unit_prices):
        if not variant_id_raw:
            continue
        qty = int(qty_raw or 0)
        if qty <= 0:
            continue
        variant = db.get(models.Variant, int(variant_id_raw))
        if not variant:
            raise HTTPException(status_code=404, detail="Product/size not found")
        if qty > variant.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Not enough stock for {variant.product.name} ({variant.label}): "
                    f"requested {qty}, only {variant.quantity} in stock"
                ),
            )
        lines.append((variant, qty, float(price_raw or 0)))

    if not lines:
        raise HTTPException(status_code=400, detail="Add at least one item to the cart")

    sale = models.Sale(total=0.0, note=note)
    db.add(sale)
    db.flush()

    total = 0.0
    for variant, qty, unit_price in lines:
        unit_cost = consume_fifo(db, variant, qty)
        sale_item = models.SaleItem(
            sale_id=sale.id,
            variant_id=variant.id,
            quantity=qty,
            unit_price=unit_price,
            unit_cost=unit_cost,
        )
        db.add(sale_item)
        db.flush()

        variant.quantity -= qty
        db.add(
            models.StockMovement(
                variant_id=variant.id,
                change=-qty,
                reason="sale",
                sale_item_id=sale_item.id,
            )
        )
        total += qty * unit_price

    sale.total = total
    db.commit()
    return RedirectResponse(f"/sales/{sale.id}", status_code=303)


@router.get("/sales")
def sales_history(
    request: Request,
    q: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    query = db.query(models.Sale)
    if q:
        like = f"%{q}%"
        matching_ids = (
            db.query(models.Sale.id)
            .outerjoin(models.SaleItem, models.SaleItem.sale_id == models.Sale.id)
            .outerjoin(models.Variant, models.Variant.id == models.SaleItem.variant_id)
            .outerjoin(models.Product, models.Product.id == models.Variant.product_id)
            .filter(or_(models.Sale.note.ilike(like), models.Product.name.ilike(like)))
            .distinct()
        )
        query = query.filter(models.Sale.id.in_(matching_ids))

    total = query.count()
    total_pages = max(1, (total + SALES_PAGE_SIZE - 1) // SALES_PAGE_SIZE)
    page = min(max(1, page), total_pages)

    sales = (
        query.order_by(models.Sale.timestamp.desc())
        .offset((page - 1) * SALES_PAGE_SIZE)
        .limit(SALES_PAGE_SIZE)
        .all()
    )

    return render(
        request,
        "sales/history.html",
        {
            "active": "sell",
            "sales": sales,
            "q": q or "",
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/sales/{sale_id}")
def sale_receipt(sale_id: int, request: Request, db: Session = Depends(get_db)):
    sale = db.get(models.Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return render(request, "sales/receipt.html", {"active": "sell", "sale": sale})
