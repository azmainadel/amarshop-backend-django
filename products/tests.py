from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from products.models import Category, Brand, Product
from products.serializers import ProductListSerializer, ProductDetailSerializer

User = get_user_model()


class ProductAPITest(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic items'
        )

        # Create test brand
        self.brand = Brand.objects.create(
            name='TestBrand',
            description='Test Brand Description'
        )

        # Create test products
        self.product1 = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name='Test Product 1',
            description='Test Description 1',
            price=99.99,
            stock=10
        )

        self.product2 = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name='Test Product 2',
            description='Test Description 2',
            price=149.99,
            stock=5
        )

        # URLs
        self.list_url = reverse('product-list')
        self.detail_url = reverse('product-detail', args=[self.product1.id])

    def test_product_list(self):
        """
        Test retrieving product list
        """
        response = self.client.get(self.list_url)
        products = Product.objects.filter(is_active=True)
        serializer = ProductListSerializer(products, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Test Product 1')
        self.assertEqual(response.data[1]['name'], 'Test Product 2')

    def test_product_detail(self):
        """
        Test retrieving product detail
        """
        response = self.client.get(self.detail_url)
        product = Product.objects.get(id=self.product1.id)
        serializer = ProductDetailSerializer(product)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.product1.name)
        self.assertEqual(response.data['price'], '99.99')
        self.assertEqual(response.data['category']['name'], 'Electronics')

    def test_product_search(self):
        """
        Test product search functionality
        """
        search_url = f"{self.list_url}?search=Test Product 1"
        response = self.client.get(search_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Product 1')

    def test_product_filter_by_price_range(self):
        """
        Test filtering products by price range
        """
        filter_url = f"{self.list_url}?min_price=100&max_price=200"
        response = self.client.get(filter_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only product2 is in this range
        self.assertEqual(response.data[0]['name'], 'Test Product 2')

    def test_inactive_product_not_shown(self):
        """
        Test that inactive products are not shown in the list
        """
        self.product1.is_active = False
        self.product1.save()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only active product shown
        self.assertEqual(response.data[0]['name'], 'Test Product 2')

    def test_invalid_product_detail(self):
        """
        Test retrieving detail for non-existent product
        """
        invalid_url = reverse('product-detail', args=[999])
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        """
        Test product ordering
        """
        # Test ordering by price ascending
        order_url = f"{self.list_url}?ordering=price"
        response = self.client.get(order_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Test Product 1')
        self.assertEqual(response.data[1]['name'], 'Test Product 2')

        # Test ordering by price descending
        order_url = f"{self.list_url}?ordering=-price"
        response = self.client.get(order_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Test Product 2')
        self.assertEqual(response.data[1]['name'], 'Test Product 1')
