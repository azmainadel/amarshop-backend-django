from rest_framework import serializers
from .models import Product, Category, Brand, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text']
        
# for product list view
class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'primary_image', 'rating']
        
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

# for product detail view
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    images = ProductImageSerializer(many=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'images', 'rating', 'category', 'brand', 'created_at']