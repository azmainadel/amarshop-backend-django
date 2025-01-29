from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('addresses/', views.AddressViewSet.as_view(), name='addresses'),
]
