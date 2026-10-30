from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem, Payment
from products.models import Brand, Category, Product
from users.models import User


class AdminApiTest(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='s@x.com', email='s@x.com', password='x', is_staff=True)
        self.customer = User.objects.create_user(username='c@x.com', email='c@x.com', password='x')
        self.category = Category.objects.create(name='C')
        self.brand = Brand.objects.create(name='B')
        self.product = Product.objects.create(name='Phone', price='100.00', stock=2, category=self.category,
                                              brand=self.brand)
        paid = Order.objects.create(user=self.customer, status='PAID', total_amount='200.00',
                                    delivery_charge='50.00', shipping_address='x')
        OrderItem.objects.create(order=paid, product=self.product, quantity=2, price='100.00')
        Payment.objects.create(order=paid, amount='250.00', payment_method='bkash', status='SUCCESS')
        self.client.force_authenticate(self.staff)

    def test_customers_are_forbidden(self):
        self.client.force_authenticate(self.customer)
        for url in ['/api/admin/users/', '/api/admin/products/', '/api/admin/transactions/',
                    '/api/admin/reports/']:
            self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN, url)

    def test_users_list_detail_update(self):
        self.assertEqual(len(self.client.get('/api/admin/users/').data), 2)
        detail = self.client.get(f'/api/admin/users/{self.customer.id}/')
        self.assertEqual(detail.data['email'], 'c@x.com')

        response = self.client.put(f'/api/admin/users/{self.customer.id}/',
                                   {'email': 'c@x.com', 'first_name': 'Cee', 'is_active': False,
                                    'is_superuser': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, 'Cee')
        self.assertFalse(self.customer.is_active)
        self.assertFalse(self.customer.is_superuser)

    def test_products_create_and_update(self):
        created = self.client.post('/api/admin/products/', {'name': 'Laptop', 'price': '500.00', 'stock': 1,
                                                            'category': self.category.id, 'brand': self.brand.id},
                                   format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        updated = self.client.put(f"/api/admin/products/{created.data['id']}/",
                                  {'name': 'Laptop', 'price': '450.00', 'stock': 3, 'is_active': False,
                                   'category': self.category.id, 'brand': self.brand.id}, format='json')
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        # Inactive products stay visible to admins.
        self.assertEqual(self.client.get(f"/api/admin/products/{created.data['id']}/").status_code,
                         status.HTTP_200_OK)

    def test_transactions_filters(self):
        self.assertEqual(len(self.client.get('/api/admin/transactions/').data), 1)
        self.assertEqual(len(self.client.get(f'/api/admin/transactions/?user={self.staff.id}').data), 0)
        self.assertEqual(len(self.client.get('/api/admin/transactions/?start_date=2000-01-01&end_date=2000-01-02').data), 0)
        self.assertEqual(self.client.get('/api/admin/transactions/?start_date=bad').status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_reports(self):
        sales = self.client.get('/api/admin/reports/?type=sales').data
        self.assertEqual(sales['paid_orders'], 1)
        self.assertEqual(sales['total_revenue'], 250)
        self.assertEqual(sales['top_products'][0]['units_sold'], 2)

        users = self.client.get('/api/admin/reports/?type=users').data
        self.assertEqual(users['total_users'], 2)
        self.assertEqual(users['orders_by_status'], {'PAID': 1})

        inventory = self.client.get('/api/admin/reports/?type=inventory').data
        self.assertEqual(inventory['low_stock'][0]['name'], 'Phone')
        self.assertEqual(inventory['stock_value'], 200)

        self.assertEqual(self.client.get('/api/admin/reports/?type=nope').status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get('/api/admin/reports/?start_date=31-12-2024').status_code,
                         status.HTTP_400_BAD_REQUEST)
