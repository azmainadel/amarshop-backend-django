from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderSerializer, CheckoutSerializer
from .models import Order, OrderItem, Payment
from .constants import DELIVERY_CHARGE
from cart.models import Cart
from users.models import Address
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    # Orders are created only through checkout, never by POSTing raw totals.
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def _process_payment(self, order: Order, payment_method):
        """Mock payment processor"""
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount + order.delivery_charge,
            payment_method=payment_method,
            transaction_id=f"test_txn_{order.id}",
            status='SUCCESS'
        )

        if payment.status == 'SUCCESS':
            order.status = 'PAID'
            order.save()

        return payment

    # def _send_order_confirmation_email(self, order):
    #     send_mail()
        
    @action(detail=False, methods=['POST'], serializer_class=CheckoutSerializer)
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.filter(user=request.user).first()
        if cart is None or not cart.items.exists():
            return Response({"error": "Cart is empty!"}, status=status.HTTP_400_BAD_REQUEST)

        address = Address.objects.get(id=serializer.validated_data['address_id'], user=request.user)

        with transaction.atomic():
            cart_items = list(cart.items.select_related('product').select_for_update())
            out_of_stock = [item.product.name for item in cart_items if item.quantity > item.product.stock]
            if out_of_stock:
                return Response({"error": f"Not enough stock for: {', '.join(out_of_stock)}"},
                                status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(
                user=request.user,
                shipping_address=str(address),
                total_amount=cart.get_total_price(),
                delivery_charge=DELIVERY_CHARGE,
                order_notes=serializer.validated_data['order_notes']
            )

            for item in cart_items:
                OrderItem.objects.create(order=order, product=item.product,
                                         quantity=item.quantity, price=item.product.price)
                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock'])

            payment = self._process_payment(order, serializer.validated_data['payment_method'])

            if payment.status != 'SUCCESS':
                transaction.set_rollback(True)
                return Response({"error": "Payment failed!"}, status=status.HTTP_402_PAYMENT_REQUIRED)

            cart.items.all().delete()

        # send email, sms
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
