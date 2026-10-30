from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from orders.models import Order
from products.models import Brand, Category, Product
from users.models import Address, User


class CheckoutAndMockPaymentTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u@x.com', email='u@x.com', password='Pass12345!')
        self.client.force_authenticate(self.user)
        category = Category.objects.create(name='C')
        brand = Brand.objects.create(name='B')
        self.product = Product.objects.create(name='Phone', price='100.00', stock=5, category=category, brand=brand)
        self.address = Address.objects.create(user=self.user, street_address='1 Rd', city='Dhaka',
                                              division='Dhaka', postal_code='1200')
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def checkout(self):
        return self.client.post('/api/order/orders/checkout/', {'address_id': self.address.id}, format='json')

    def pay(self, order_id, **info):
        return self.client.post('/api/order/orders/payment/mock/',
                                {'order_id': order_id, 'payment_method': 'bkash', 'payment_info': info},
                                format='json')

    def test_checkout_creates_pending_order_and_reserves_stock(self):
        response = self.checkout()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(response.data['total_amount'], '200.00')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(CartItem.objects.exists())

    def test_mock_payment_pays_order(self):
        order_id = self.checkout().data['id']
        response = self.pay(order_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PAID')
        self.assertEqual(response.data['payment']['amount'], '250.00')

        again = self.pay(order_id)
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_payment_can_be_retried(self):
        order_id = self.checkout().data['id']
        failed = self.pay(order_id, simulate='fail')
        self.assertEqual(failed.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(Order.objects.get(id=order_id).status, 'PENDING')

        self.assertEqual(self.pay(order_id).status_code, status.HTTP_200_OK)

    def test_cannot_pay_another_users_order(self):
        order_id = self.checkout().data['id']
        other = User.objects.create_user(username='o@x.com', email='o@x.com', password='Pass12345!')
        self.client.force_authenticate(other)
        self.assertEqual(self.pay(order_id).status_code, status.HTTP_404_NOT_FOUND)
