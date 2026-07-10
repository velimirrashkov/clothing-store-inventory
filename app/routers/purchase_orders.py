import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from ..templating import render

router = APIRouter(prefix="/purchase-orders")

NEW_ORDER_BLANK_ROWS = 8


@router.get("")
def list_purchase_orders(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(models.PurchaseOrder)
        .join(models.Supplier)
        .options(joinedload(models.PurchaseOrder.supplier))
    )
    if q:
        query = query.filter(models.Supplier.name.ilike(f"%{q}%"))
    orders = query.order_by(models.PurchaseOrder.created_at.desc()).all()
    return render(
        request,
        "purchase_orders/index.html",
        {"active": "purchase_orders", "orders": orders, "q": q or ""},
    )


def _variant_choices(db: Session):
    variants = (
        db.query(models.Variant)
        .join(models.Product)
        .options(joinedload(models.Variant.product))
        .order_by(models.Product.name, models.Variant.size)
        .all()
    )
    return variants


@router.get("/new")
def new_purchase_order_form(
    request: Request, supplier_id: Optional[int] = None, db: Session = Depends(get_db)
):
    suppliers = db.query(models.Supplier).order_by(models.Supplier.name).all()
    if not suppliers:
        raise HTTPException(
            status_code=400, detail="Add a supplier first before creating a purchase order"
        )

    supplier = None
    cost_map = {}
    if supplier_id:
        supplier = db.get(models.Supplier, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        links = (
            db.query(models.ProductSupplier)
            .filter(models.ProductSupplier.supplier_id == supplier_id)
            .all()
        )
        cost_map = {link.product_id: link.cost_price for link in links}

    variants = _variant_choices(db)

    return render(
        request,
        "purchase_orders/form.html",
        {
            "active": "purchase_orders",
            "suppliers": suppliers,
            "supplier": supplier,
            "variants": variants,
            "cost_map": cost_map,
            "blank_rows": range(NEW_ORDER_BLANK_ROWS),
        },
    )


@router.post("/new")
def create_purchase_order(
    supplier_id: int = Form(...),
    notes: str = Form(""),
    variant_ids: list = Form([]),
    quantities: list = Form([]),
    unit_costs: list = Form([]),
    db: Session = Depends(get_db),
):
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    order = models.PurchaseOrder(supplier_id=supplier_id, status="draft", notes=notes)
    db.add(order)
    db.flush()

    added_lines = 0
    for variant_id_raw, qty_raw, cost_raw in zip(variant_ids, quantities, unit_costs):
        if not variant_id_raw:
            continue
        qty = int(qty_raw or 0)
        if qty <= 0:
            continue
        variant = db.get(models.Variant, int(variant_id_raw))
        if not variant:
            continue
        db.add(
            models.PurchaseOrderLine(
                purchase_order_id=order.id,
                variant_id=variant.id,
                quantity_ordered=qty,
                unit_cost=float(cost_raw or 0),
            )
        )
        added_lines += 1

    if added_lines == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Add at least one line item with a quantity")

    db.commit()
    return RedirectResponse(f"/purchase-orders/{order.id}", status_code=303)


@router.get("/{order_id}")
def purchase_order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.get(models.PurchaseOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return render(
        request, "purchase_orders/detail.html", {"active": "purchase_orders", "order": order}
    )


@router.post("/{order_id}/mark-ordered")
def mark_ordered(order_id: int, db: Session = Depends(get_db)):
    order = db.get(models.PurchaseOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft orders can be marked as ordered")
    order.status = "ordered"
    order.ordered_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/purchase-orders/{order_id}", status_code=303)


@router.post("/{order_id}/receive")
def receive_purchase_order(
    order_id: int,
    line_ids: list = Form([]),
    receive_quantities: list = Form([]),
    receive_costs: list = Form([]),
    db: Session = Depends(get_db),
):
    order = db.get(models.PurchaseOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status not in ("ordered", "partial"):
        raise HTTPException(
            status_code=400, detail="Only ordered or partially received orders can be received"
        )

    any_received = False
    for line_id_raw, qty_raw, cost_raw in zip(line_ids, receive_quantities, receive_costs):
        qty = int(qty_raw or 0)
        if qty <= 0:
            continue
        line = db.get(models.PurchaseOrderLine, int(line_id_raw))
        if not line or line.purchase_order_id != order_id:
            continue
        qty = min(qty, line.quantity_remaining)
        if qty <= 0:
            continue
        unit_cost = float(cost_raw or line.unit_cost)

        db.add(
            models.StockBatch(
                variant_id=line.variant_id,
                purchase_order_line_id=line.id,
                quantity_received=qty,
                quantity_remaining=qty,
                buy_price=unit_cost,
            )
        )
        line.variant.quantity += qty
        line.quantity_received += qty
        db.add(
            models.StockMovement(
                variant_id=line.variant_id,
                change=qty,
                reason="received",
                purchase_order_line_id=line.id,
            )
        )
        any_received = True

    if not any_received:
        raise HTTPException(status_code=400, detail="Enter a quantity to receive for at least one line")

    if order.is_fully_received:
        order.status = "received"
        order.received_at = datetime.datetime.utcnow()
    else:
        order.status = "partial"

    db.commit()
    return RedirectResponse(f"/purchase-orders/{order_id}", status_code=303)


@router.post("/{order_id}/cancel")
def cancel_purchase_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(models.PurchaseOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status == "received":
        raise HTTPException(status_code=400, detail="Cannot cancel a fully received order")
    order.status = "cancelled"
    db.commit()
    return RedirectResponse(f"/purchase-orders/{order_id}", status_code=303)
