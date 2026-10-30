from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from .models import Category, Brand, Product
from .serializers import CategorySerializer, BrandSerializer, ProductImageSerializer, ProductDetailSerializer, ProductListSerializer, ProductWriteSerializer
from .filters import ProductFilter


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    
    # USING RAW SQL
    # queryset = Product.objects.raw(
    #     '''
    #     SELECT * FROM products_product
    #     WHERE is_active = TRUE
    #     '''
    # )
    
    # AUTOMATIC CACHING
    # @method_decorator(cache_page(60*30))
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)
    
    # MANUAL CACHING
    # def list(self, request, *args, **kwargs):
    #     cache_key = f'product_list_{request.user.id}'
    #     cached_data = cache.get(cache_key)
        
    #     if cached_data is not None:
    #         return cached_data
        
    #     response = super().list(request, *args, **kwargs)
    #     cache.set(cache_key, response.data, timeout=60*30)
    #     return response
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter

    search_fields = ['name', 'description', 'brand__name', 'category__name']
    ordering_fields = ['price', 'rating']

    @action(detail=False, methods=['POST'])
    def search(self, request):
        """POST {"searchTerm": "..."}: same fields as GET ?search=."""
        term = str(request.data.get('searchTerm', '')).strip()
        if not term:
            return Response({'searchTerm': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        query = Q()
        for word in term.split():
            word_query = Q()
            for field in self.search_fields:
                word_query |= Q(**{f'{field}__icontains': word})
            query &= word_query

        products = self.get_queryset().filter(query).distinct()
        return Response(ProductListSerializer(products, many=True).data)

    @action(detail=False, methods=['POST'], url_path='filter')
    def filter_products(self, request):
        """POST body takes the same keys as the GET filters: category, brand, min_price, max_price, min_rating."""
        product_filter = ProductFilter(data=request.data, queryset=self.get_queryset())
        if not product_filter.is_valid():
            return Response(product_filter.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductListSerializer(product_filter.qs, many=True).data)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProductWriteSerializer
        return ProductListSerializer
