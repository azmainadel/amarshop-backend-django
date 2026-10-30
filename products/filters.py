import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    category = django_filters.NumberFilter(field_name='category_id')
    brand = django_filters.NumberFilter(field_name='brand_id')
    
    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'min_rating', 'category', 'brand']
