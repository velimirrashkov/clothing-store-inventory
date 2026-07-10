from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import hash_password, verify_password
from ..database import get_db
from ..templating import render

router = APIRouter()


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)

    is_first_run = db.query(models.User).count() == 0
    return render(
        request,
        "auth/login.html",
        {"is_first_run": is_first_run, "error": None},
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(""),
    db: Session = Depends(get_db),
):
    is_first_run = db.query(models.User).count() == 0

    if is_first_run:
        username = username.strip()
        if not username or not password:
            return render(
                request,
                "auth/login.html",
                {"is_first_run": True, "error": "missing_fields"},
                status_code=400,
            )
        if password != confirm_password:
            return render(
                request,
                "auth/login.html",
                {"is_first_run": True, "error": "password_mismatch"},
                status_code=400,
            )
        user = models.User(
            username=username,
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(user)
        db.commit()
        request.session["user_id"] = user.id
        return RedirectResponse("/", status_code=303)

    user = db.query(models.User).filter(models.User.username == username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return render(
            request,
            "auth/login.html",
            {"is_first_run": False, "error": "invalid_credentials"},
            status_code=400,
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
