"""
ALL business logic for pricing. Public function surface of the app (see architecture-spec.md §2.1).

`calculate_cart_total` (full subtotal/discount/shipping/tax breakdown for online checkout) is a
Phase 2 seam — see architecture-spec.md §8.4 — landing alongside cart/checkout in `orders`.
`extract_vat` below is the narrower Phase 1 need: POS prices are VAT-inclusive, so tax_amount
is derived from the total for receipts/reporting, never added on top (see §5.5-adjacent design
note on overselling, and the POS flow in `apps.orders.services.create_pos_order`).
"""
from django.conf import settings


def extract_vat(gross_amount: int, rate: float | None = None) -> int:
    """
    gross_amount is VAT-inclusive, in minor units. Returns the VAT component, in minor units,
    rounded to the nearest minor unit (never a float in the stored result — see §4.1).
    """
    rate = settings.VAT_RATE if rate is None else rate
    return round(gross_amount * rate / (1 + rate))
