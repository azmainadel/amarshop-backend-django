from rest_framework import serializers
from users.models import User
from users.serializers import AddressSerializer
from orders.models import Payment


class AdminUserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'addresses',
                  'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        # Promoting to superuser is left to the Django admin site / createsuperuser.
        read_only_fields = ['id', 'is_superuser', 'date_joined', 'last_login']


class TransactionSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    user_id = serializers.IntegerField(source='order.user_id', read_only=True)
    user_email = serializers.EmailField(source='order.user.email', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'order_status', 'user_id', 'user_email', 'amount',
                  'payment_method', 'transaction_id', 'status', 'created_at']
