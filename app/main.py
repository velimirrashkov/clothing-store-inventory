import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import Forbidden, NotAuthenticated, require_login, require_role
from .database import Base, engine
from .paths import SESSION_SECRET_FILE, STATIC_DIR
from .templating import render
from .routers import (
    auth_routes,
    categories,
    inventory,
    lang,
    purchase_orders,
    reports,
    sales,
    suppliers,
    users,
)

Base.metadata.create_all(bind=engine)


def _load_or_create_session_secret() -> str:
    if SESSION_SECRET_FILE.exists():
        return SESSION_SECRET_FILE.read_text().strip()
    secret = secrets.token_hex(32)
    SESSION_SECRET_FILE.write_text(secret)
    return secret


app = FastAPI(title="Clothing Store Inventory")
app.add_middleware(SessionMiddleware, secret_key=_load_or_create_session_secret())
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(NotAuthenticated)
def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
def forbidden_handler(request: Request, exc: Forbidden):
    return render(request, "auth/forbidden.html", {}, status_code=403)


app.include_router(lang.router)
app.include_router(auth_routes.router)
app.include_router(inventory.router, dependencies=[Depends(require_login)])
app.include_router(sales.router, dependencies=[Depends(require_login)])
app.include_router(categories.router, dependencies=[Depends(require_role("admin"))])
app.include_router(suppliers.router, dependencies=[Depends(require_role("admin"))])
app.include_router(purchase_orders.router, dependencies=[Depends(require_role("admin"))])
app.include_router(reports.router, dependencies=[Depends(require_role("admin"))])
app.include_router(users.router, dependencies=[Depends(require_role("admin"))])
