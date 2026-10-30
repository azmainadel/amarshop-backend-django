from decimal import Decimal

# Decimal, not float: it's added to DecimalField values (Decimal + float raises TypeError).
DELIVERY_CHARGE = Decimal('50.00')
