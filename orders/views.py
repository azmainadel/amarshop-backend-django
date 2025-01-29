from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .serializers import OrderSerializer, CheckoutSerializer
from .models import Order, Payment
from .constants import DELIVERY_CHARGE
from cart.models import Cart
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

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
        
    @action(detail=False, methods=['POST'])
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            cart = Cart.objects.filter(user=request.user)
            
            if not cart.items.exists():
                return Response({"error": "Cart is empty!"}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(
                user=request.user,
                # TODO set shipping address
                total_amount=cart.get_total_price(),
                delivery_charge=DELIVERY_CHARGE,
                order_notes=serializer.validated_data['order_notes']
            )
            
            payment = self._process_payment(order, serializer.validated_data['payment_method'])
            
            if payment.status == 'SUCCESS':
                cart.items.all().delete()
                # send email, sms
                return Response(status=status.HTTP_201_CREATED)
            
            return Response({"error": "Payment failed!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            