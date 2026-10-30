from rest_framework import serializers
from .models import Cart, CartItem, SavedItem
from products.serializers import ProductListSerializer
from products.models import Product


def _get_active_product(product_id):
    try:
        return Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        raise serializers.ValidationError("Product not found") from None


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    price = serializers.DecimalField(decimal_places=2, max_digits=10, read_only=True, source='get_price')

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price']
        read_only_fields = ['id', 'price']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value

    def validate(self, attrs):
        # On update the product comes from the existing item; on add it comes from the payload.
        if self.instance is not None:
            product = self.instance.product
        else:
            try:
                product = _get_active_product(attrs.get('product_id'))
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({'product_id': exc.detail}) from None

        quantity = attrs.get('quantity', self.instance.quantity if self.instance else 1)
        # Quantity already in the cart counts towards stock when adding the same product again.
        existing = self.context.get('existing_quantity', 0)
        if quantity + existing > product.stock:
            raise serializers.ValidationError({'quantity': f"Only {product.stock} items available in stock"})

        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(decimal_places=2, max_digits=10, read_only=True, source='get_total_price')
    total_quantity = serializers.IntegerField(read_only=True, source='get_total_quantity')

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_quantity']


class SavedItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SavedItem
        fields = ['id', 'product', 'product_id']
        read_only_fields = ['id']

    def validate_product_id(self, value):
        _get_active_product(value)
        return value
