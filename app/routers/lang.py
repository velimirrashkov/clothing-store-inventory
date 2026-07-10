from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..i18n import DEFAULT_LANG, LANG_COOKIE, SUPPORTED_LANGS

router = APIRouter()


@router.get("/lang/{code}")
def set_lang(code: str, request: Request):
    if code not in SUPPORTED_LANGS:
        code = DEFAULT_LANG
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(referer, status_code=303)
    response.set_cookie(LANG_COOKIE, code, max_age=60 * 60 * 24 * 365)
    return response
