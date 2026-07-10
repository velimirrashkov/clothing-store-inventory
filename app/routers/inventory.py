import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..queries import build_category_tree, ordered_categories
from ..templating import render

router = APIRouter()


def _sku_part(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "", text or "").upper()
    return slug[:6] if slug else "STD"


def _generate_variant_sku(db: Session, style_code: str, size: str, color: str) -> str:
    base = f"{style_code}-{_sku_part(size)}"
    if color:
        base = f"{base}-{_sku_part(color)}"
    candidate = base
    suffix = 2
    while db.query(models.Variant).filter(models.Variant.sku == candidate).first():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    category_tree = build_category_tree(db)

    products = db.query(models.Product).order_by(models.Product.name).all()
    catalog = [
        {
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
        }
        for p in products
    ]

    return render(
        request,
        "products/index.html",
        {
            "active": "inventory",
            "category_tree_json": json.dumps(category_tree),
            "catalog_json": json.dumps(catalog),
        },
    )


@router.get("/products/{product_id}/panel")
def product_detail_panel(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    recent_movements = (
        db.query(models.StockMovement)
        .join(models.Variant)
        .filter(models.Variant.product_id == product_id)
        .order_by(models.StockMovement.timestamp.desc())
        .limit(20)
        .all()
    )

    linked_supplier_ids = {link.supplier_id for link in product.supplier_links}
    available_suppliers = (
        db.query(models.Supplier)
        .filter(~models.Supplier.id.in_(linked_supplier_ids) if linked_supplier_ids else True)
        .order_by(models.Supplier.name)
        .all()
    )

    return render(
        request,
        "products/_detail_panel.html",
        {
            "product": product,
            "movements": recent_movements,
            "low_stock_threshold": models.LOW_STOCK_THRESHOLD,
            "standard_sizes": models.STANDARD_SIZES,
            "available_suppliers": available_suppliers,
        },
    )


@router.get("/products/new")
def new_product_form(request: Request, db: Session = Depends(get_db)):
    return render(
        request,
        "products/form.html",
        {
            "active": "inventory",
            "product": None,
            "genders": models.GENDERS,
            "standard_sizes": models.STANDARD_SIZES,
            "statuses": models.PRODUCT_STATUSES,
            "categories": ordered_categories(db),
        },
    )


@router.post("/products/new")
def create_product(
    name: str = Form(...),
    style_code: str = Form(...),
    gender: str = Form(...),
    category_id: str = Form(""),
    sell_price: float = Form(0.0),
    description: str = Form(""),
    material_composition: str = Form(""),
    care_instructions: str = Form(""),
    season: str = Form(""),
    status: str = Form("active"),
    sizes: list = Form([]),
    colors: list = Form([]),
    quantities: list = Form([]),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Product).filter(models.Product.style_code == style_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Style code '{style_code}' already exists")

    product = models.Product(
        name=name,
        style_code=style_code,
        gender=gender,
        category_id=int(category_id) if category_id else None,
        sell_price=sell_price,
        description=description,
        material_composition=material_composition,
        care_instructions=care_instructions,
        season=season,
        status=status,
    )
    db.add(product)
    db.flush()

    for size, color, qty in zip(sizes, colors, quantities):
        size = size.strip()
        color = (color or "").strip()
        if not size:
            continue
        qty_int = int(qty or 0)
        variant = models.Variant(
            product_id=product.id,
            size=size,
            color_name=color,
            sku=_generate_variant_sku(db, style_code, size, color),
            quantity=qty_int,
        )
        db.add(variant)
        db.flush()
        if qty_int:
            db.add(
                models.StockMovement(
                    variant_id=variant.id,
                    change=qty_int,
                    reason="initial_stock",
                )
            )

    db.commit()
    return RedirectResponse(f"/products/{product.id}", status_code=303)


@router.get("/products/{product_id}")
def product_detail(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    recent_movements = (
        db.query(models.StockMovement)
        .join(models.Variant)
        .filter(models.Variant.product_id == product_id)
        .order_by(models.StockMovement.timestamp.desc())
        .limit(20)
        .all()
    )

    linked_supplier_ids = {link.supplier_id for link in product.supplier_links}
    available_suppliers = (
        db.query(models.Supplier)
        .filter(~models.Supplier.id.in_(linked_supplier_ids) if linked_supplier_ids else True)
        .order_by(models.Supplier.name)
        .all()
    )

    return render(
        request,
        "products/detail.html",
        {
            "active": "inventory",
            "product": product,
            "movements": recent_movements,
            "low_stock_threshold": models.LOW_STOCK_THRESHOLD,
            "standard_sizes": models.STANDARD_SIZES,
            "available_suppliers": available_suppliers,
        },
    )


@router.get("/products/{product_id}/edit")
def edit_product_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return render(
        request,
        "products/form.html",
        {
            "active": "inventory",
            "product": product,
            "genders": models.GENDERS,
            "standard_sizes": models.STANDARD_SIZES,
            "statuses": models.PRODUCT_STATUSES,
            "categories": ordered_categories(db),
        },
    )


@router.post("/products/{product_id}/edit")
def update_product(
    product_id: int,
    name: str = Form(...),
    style_code: str = Form(...),
    gender: str = Form(...),
    category_id: str = Form(""),
    sell_price: float = Form(0.0),
    description: str = Form(""),
    material_composition: str = Form(""),
    care_instructions: str = Form(""),
    season: str = Form(""),
    status: str = Form("active"),
    db: Session = Depends(get_db),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    duplicate = (
        db.query(models.Product)
        .filter(models.Product.style_code == style_code, models.Product.id != product_id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=400, detail=f"Style code '{style_code}' already exists")

    product.name = name
    product.style_code = style_code
    product.gender = gender
    product.category_id = int(category_id) if category_id else None
    product.sell_price = sell_price
    product.description = description
    product.material_composition = material_composition
    product.care_instructions = care_instructions
    product.season = season
    product.status = status
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/delete")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/products/{product_id}/stock")
def adjust_stock(
    product_id: int,
    variant_id: int = Form(...),
    delta: int = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    variant = db.get(models.Variant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=404, detail="Variant not found")

    new_quantity = variant.quantity + delta
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below zero")

    variant.quantity = new_quantity
    db.add(
        models.StockMovement(
            variant_id=variant.id, change=delta, reason="adjustment", note=note
        )
    )
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/variants/add")
def add_variant(
    product_id: int,
    size: str = Form(...),
    color: str = Form(""),
    quantity: int = Form(0),
    db: Session = Depends(get_db),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    size = size.strip()
    color = (color or "").strip()
    existing = (
        db.query(models.Variant)
        .filter(
            models.Variant.product_id == product_id,
            models.Variant.size == size,
            models.Variant.color_name == color,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="This size/colour combination already exists")

    variant = models.Variant(
        product_id=product_id,
        size=size,
        color_name=color,
        sku=_generate_variant_sku(db, product.style_code, size, color),
        quantity=quantity,
    )
    db.add(variant)
    db.flush()
    if quantity:
        db.add(
            models.StockMovement(
                variant_id=variant.id, change=quantity, reason="initial_stock"
            )
        )
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/variants/{variant_id}/edit-meta")
def edit_variant_meta(
    product_id: int,
    variant_id: int,
    sku: str = Form(...),
    barcode: str = Form(""),
    color_hex: str = Form(""),
    db: Session = Depends(get_db),
):
    variant = db.get(models.Variant, variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=404, detail="Variant not found")

    duplicate = (
        db.query(models.Variant)
        .filter(models.Variant.sku == sku, models.Variant.id != variant_id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=400, detail=f"SKU '{sku}' already in use")

    variant.sku = sku
    variant.barcode = barcode
    variant.color_hex = color_hex or None
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/suppliers/add")
def add_product_supplier(
    product_id: int,
    supplier_id: int = Form(...),
    cost_price: float = Form(0.0),
    supplier_sku: str = Form(""),
    db: Session = Depends(get_db),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    supplier = db.get(models.Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    existing = (
        db.query(models.ProductSupplier)
        .filter(
            models.ProductSupplier.product_id == product_id,
            models.ProductSupplier.supplier_id == supplier_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Supplier already linked to this product")

    link = models.ProductSupplier(
        product_id=product_id,
        supplier_id=supplier_id,
        cost_price=cost_price,
        supplier_sku=supplier_sku,
    )
    db.add(link)
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/suppliers/{link_id}/edit")
def edit_product_supplier(
    product_id: int,
    link_id: int,
    cost_price: float = Form(0.0),
    supplier_sku: str = Form(""),
    db: Session = Depends(get_db),
):
    link = db.get(models.ProductSupplier, link_id)
    if not link or link.product_id != product_id:
        raise HTTPException(status_code=404, detail="Supplier link not found")
    link.cost_price = cost_price
    link.supplier_sku = supplier_sku
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/suppliers/{link_id}/remove")
def remove_product_supplier(product_id: int, link_id: int, db: Session = Depends(get_db)):
    link = db.get(models.ProductSupplier, link_id)
    if not link or link.product_id != product_id:
        raise HTTPException(status_code=404, detail="Supplier link not found")
    db.delete(link)
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/attributes/add")
def add_attribute(
    product_id: int,
    key: str = Form(...),
    value: str = Form(""),
    db: Session = Depends(get_db),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    key = key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Attribute name cannot be empty")
    db.add(models.ProductAttribute(product_id=product_id, key=key, value=value.strip()))
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/attributes/{attribute_id}/remove")
def remove_attribute(product_id: int, attribute_id: int, db: Session = Depends(get_db)):
    attribute = db.get(models.ProductAttribute, attribute_id)
    if not attribute or attribute.product_id != product_id:
        raise HTTPException(status_code=404, detail="Attribute not found")
    db.delete(attribute)
    db.commit()
    return RedirectResponse(f"/products/{product_id}", status_code=303)
