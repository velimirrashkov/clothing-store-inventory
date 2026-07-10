from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..i18n import get_lang
from ..templating import render

router = APIRouter(prefix="/reports")

RANGE_DAYS = {"today": 1, "7d": 7, "30d": 30}

BG_MONTHS = ["яну", "фев", "мар", "апр", "май", "юни", "юли", "авг", "сеп", "окт", "ное", "дек"]


def _format_day(d: date, lang: str) -> str:
    if lang == "bg":
        return f"{d.day} {BG_MONTHS[d.month - 1]}"
    return d.strftime("%b %d")


def _resolve_range(range_key: str, start: Optional[str], end: Optional[str]):
    today = datetime.utcnow().date()
    if range_key == "custom" and start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        days = RANGE_DAYS.get(range_key, 7)
        start_date = today - timedelta(days=days - 1)
        end_date = today
    return start_date, end_date


@router.get("")
def reports(
    request: Request,
    range: str = "7d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _resolve_range(range, start, end)
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    sales = (
        db.query(models.Sale)
        .filter(models.Sale.timestamp >= start_dt, models.Sale.timestamp <= end_dt)
        .all()
    )

    revenue = sum(s.total for s in sales)
    cost = sum(s.total_cost for s in sales)
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue else 0.0

    daily_totals = {}
    d = start_date
    while d <= end_date:
        daily_totals[d] = 0.0
        d += timedelta(days=1)
    for s in sales:
        sale_date = s.timestamp.date()
        if sale_date in daily_totals:
            daily_totals[sale_date] += s.total

    lang = get_lang(request)
    sorted_days = sorted(daily_totals)
    label_every = max(1, len(sorted_days) // 10)
    daily_series = [
        {
            "label": _format_day(d, lang) if i % label_every == 0 else "",
            "full_label": _format_day(d, lang),
            "revenue": daily_totals[d],
        }
        for i, d in enumerate(sorted_days)
    ]
    max_daily_revenue = max((d["revenue"] for d in daily_series), default=0) or 1.0

    item_totals = {}
    for s in sales:
        for item in s.items:
            key = item.variant.product.id
            agg = item_totals.setdefault(
                key, {"name": item.variant.product.name, "qty": 0, "revenue": 0.0}
            )
            agg["qty"] += item.quantity
            agg["revenue"] += item.line_total
    top_products = sorted(item_totals.values(), key=lambda x: x["qty"], reverse=True)[:5]

    all_products = db.query(models.Product).order_by(models.Product.name).all()
    inventory_value = sum(p.inventory_value for p in all_products)

    return render(
        request,
        "reports/index.html",
        {
            "active": "reports",
            "range": range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "margin": margin,
            "daily_series": daily_series,
            "max_daily_revenue": max_daily_revenue,
            "top_products": top_products,
            "inventory_value": inventory_value,
        },
    )
