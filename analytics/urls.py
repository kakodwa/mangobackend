# analytics/urls.py
from django.urls import path
from .api.admin_views import AdminDashboardView
from .api.customer_views import CustomerDashboardView
from .api.shop_views import ShopDashboardView
from .api.property_views import PropertyDashboardView
from .api.delivery_views import DeliveryDashboardView

urlpatterns = [
    path('admin/dashboard/', AdminDashboardView.as_view()),
    path('customer/dashboard/', CustomerDashboardView.as_view()),
    path('shop/dashboard/', ShopDashboardView.as_view()),
    path('property/dashboard/', PropertyDashboardView.as_view()),
    path('delivery/dashboard/', DeliveryDashboardView.as_view()),
]