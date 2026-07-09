from decimal import Decimal, ROUND_HALF_UP


def round_money(value: Decimal) -> Decimal:
    """Redondea un valor monetario a 2 decimales con la regla ROUND_HALF_UP."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
