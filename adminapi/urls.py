from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', viewset=views.AdminUserViewSet, basename='admin-user')
router.register(r'products', viewset=views.AdminProductViewSet, basename='admin-product')
router.register(r'transactions', viewset=views.AdminTransactionViewSet, basename='admin-transaction')

urlpatterns = [
    path('reports/', views.AdminReportView.as_view(), name='admin-reports'),
    path('', include(router.urls)),
]
