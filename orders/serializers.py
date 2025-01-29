from rest_framework import serializers
from .models import Order, OrderItem, Payment
from products.serializers import ProductListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'transaction_id', 'status', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='get_total_price')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    # TODO Task: set shipping_address using some serialization

    class Meta:
        model = Order
        fields = ['id', 'status', 'items', 'total_amount',
                  'delivery_charge', 'shipping_address', 'payment', 'created_at']

# TODO Task: Write the checkout serializer
# Sample serialized data = {
#    "address_id": 123,
#    "payment_method": "bkash",
#    "order_notes": " "
# }
class CheckoutSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    order_notes = serializers.CharField(required=False, allow_blank=True)