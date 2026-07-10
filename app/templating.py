from fastapi import Request
from fastapi.templating import Jinja2Templates

from .i18n import get_lang, translator
from .paths import TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def render(request: Request, template_name: str, context: dict = None, status_code: int = 200):
    context = dict(context or {})
    lang = get_lang(request)
    context["request"] = request
    context["lang"] = lang
    context["t"] = translator(lang)
    context["current_user"] = getattr(request.state, "user", None)
    return templates.TemplateResponse(template_name, context, status_code=status_code)
