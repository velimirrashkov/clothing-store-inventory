from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..templating import render

router = APIRouter(prefix="/suppliers")


@router.get("")
def list_suppliers(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Supplier)
    if q:
        query = query.filter(models.Supplier.name.ilike(f"%{q}%"))
    suppliers = query.order_by(models.Supplier.name).all()
    return render(
        request,
        "suppliers/index.html",
        {"active": "suppliers", "suppliers": suppliers, "q": q or ""},
    )


@router.get("/new")
def new_supplier_form(request: Request):
    return render(
        request, "suppliers/form.html", {"active": "suppliers", "supplier": None}
    )


@router.post("/new")
def create_supplier(
    name: str = Form(...),
    contact_name: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    supplier = models.Supplier(
        name=name,
        contact_name=contact_name,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
    )
    db.add(supplier)
    db.commit()
    return RedirectResponse(f"/suppliers/{supplier.id}", status_code=303)


@router.get("/{supplier_id}")
def supplier_detail(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    purchase_orders = (
        db.query(models.PurchaseOrder)
        .filter(models.PurchaseOrder.supplier_id == supplier_id)
        .order_by(models.PurchaseOrder.created_at.desc())
        .all()
    )

    return render(
        request,
        "suppliers/detail.html",
        {
            "active": "suppliers",
            "supplier": supplier,
            "purchase_orders": purchase_orders,
        },
    )


@router.get("/{supplier_id}/edit")
def edit_supplier_form(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return render(
        request, "suppliers/form.html", {"active": "suppliers", "supplier": supplier}
    )


@router.post("/{supplier_id}/edit")
def update_supplier(
    supplier_id: int,
    name: str = Form(...),
    contact_name: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.name = name
    supplier.contact_name = contact_name
    supplier.phone = phone
    supplier.email = email
    supplier.address = address
    supplier.notes = notes
    db.commit()
    return RedirectResponse(f"/suppliers/{supplier_id}", status_code=303)


@router.post("/{supplier_id}/delete")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    has_pos = (
        db.query(models.PurchaseOrder)
        .filter(models.PurchaseOrder.supplier_id == supplier_id)
        .first()
    )
    if has_pos:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a supplier with purchase order history. Cancel or remove their purchase orders first.",
        )

    db.delete(supplier)
    db.commit()
    return RedirectResponse("/suppliers", status_code=303)
