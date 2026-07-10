from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..queries import ordered_categories
from ..templating import render

router = APIRouter(prefix="/categories")


@router.get("")
def list_categories(request: Request, db: Session = Depends(get_db)):
    roots = (
        db.query(models.Category)
        .filter(models.Category.parent_id.is_(None))
        .order_by(models.Category.name)
        .all()
    )
    return render(request, "categories/index.html", {"active": "categories", "roots": roots})


@router.get("/new")
def new_category_form(request: Request, db: Session = Depends(get_db)):
    categories = ordered_categories(db)
    return render(
        request,
        "categories/form.html",
        {"active": "categories", "category": None, "categories": categories},
    )


@router.post("/new")
def create_category(
    name: str = Form(...),
    parent_id: str = Form(""),
    db: Session = Depends(get_db),
):
    parent = db.get(models.Category, int(parent_id)) if parent_id else None
    category = models.Category(name=name, parent_id=parent.id if parent else None)
    db.add(category)
    db.commit()
    return RedirectResponse("/categories", status_code=303)


@router.get("/{category_id}/edit")
def edit_category_form(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = db.get(models.Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    categories = [c for c in ordered_categories(db) if c.id != category_id]
    return render(
        request,
        "categories/form.html",
        {"active": "categories", "category": category, "categories": categories},
    )


@router.post("/{category_id}/edit")
def update_category(
    category_id: int,
    name: str = Form(...),
    parent_id: str = Form(""),
    db: Session = Depends(get_db),
):
    category = db.get(models.Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_parent_id = int(parent_id) if parent_id else None
    if new_parent_id == category_id:
        raise HTTPException(status_code=400, detail="A category cannot be its own parent")

    category.name = name
    category.parent_id = new_parent_id
    db.commit()
    return RedirectResponse("/categories", status_code=303)


@router.post("/{category_id}/delete")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(models.Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.children:
        raise HTTPException(
            status_code=400, detail="Remove or reassign subcategories before deleting this category"
        )
    if category.products:
        raise HTTPException(
            status_code=400, detail="Reassign products in this category before deleting it"
        )

    db.delete(category)
    db.commit()
    return RedirectResponse("/categories", status_code=303)
