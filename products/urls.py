from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', viewset=views.CategoryViewSet)
router.register(r'brands', viewset=views.BrandViewSet)
router.register(r'products', viewset=views.ProductViewSet)

urlpatterns = [
    path('', include(router.urls))
] 
