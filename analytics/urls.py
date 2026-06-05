# analytics/urls.py
from django.urls import path
from .views import LogEventView, GetStatsView,remove_product_background

urlpatterns = [
    path('log/', LogEventView.as_view(), name='log_event'),
    path('stats/', GetStatsView.as_view(), name='get_stats'),
    path('api/remove-bg/',remove_product_background, name='remove_bg'),
]