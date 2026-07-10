from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import hash_password, require_role
from ..database import get_db
from ..templating import render

router = APIRouter(prefix="/users")


@router.get("")
def list_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.username).all()
    return render(request, "users/index.html", {"active": "users", "users": users})


@router.get("/new")
def new_user_form(request: Request):
    return render(
        request, "users/form.html", {"active": "users", "user": None, "roles": models.ROLES}
    )


@router.post("/new")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{username}' already exists")
    if role not in models.ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = models.User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    return RedirectResponse("/users", status_code=303)


@router.get("/{user_id}/edit")
def edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return render(
        request, "users/form.html", {"active": "users", "user": user, "roles": models.ROLES}
    )


@router.post("/{user_id}/edit")
def update_user(
    user_id: int,
    username: str = Form(...),
    password: str = Form(""),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    username = username.strip()
    duplicate = (
        db.query(models.User)
        .filter(models.User.username == username, models.User.id != user_id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=400, detail=f"Username '{username}' already exists")
    if role not in models.ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    if user.role == "admin" and role != "admin":
        remaining_admins = (
            db.query(models.User)
            .filter(models.User.role == "admin", models.User.id != user_id)
            .count()
        )
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="Cannot remove the last remaining admin")

    user.username = username
    user.role = role
    if password:
        user.password_hash = hash_password(password)
    db.commit()
    return RedirectResponse("/users", status_code=303)


@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin")),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    if user.role == "admin":
        remaining_admins = (
            db.query(models.User)
            .filter(models.User.role == "admin", models.User.id != user_id)
            .count()
        )
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="Cannot delete the last remaining admin")

    db.delete(user)
    db.commit()
    return RedirectResponse("/users", status_code=303)
