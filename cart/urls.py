from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cart', viewset=views.CartViewSet, basename='cart')
router.register(r'saved_item', viewset=views.SavedItemViewSet, basename='saved_item')

urlpatterns = [
    path('', include(router.urls))
] 
