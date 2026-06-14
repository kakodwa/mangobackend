# analytics/urls.py
from django.urls import path
from .views import LogEventView, GetStatsView

urlpatterns = [
    path('log/', LogEventView.as_view(), name='log_event'),
    path('stats/', GetStatsView.as_view(), name='get_stats'),
]

