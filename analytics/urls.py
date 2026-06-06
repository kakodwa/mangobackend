# analytics/urls.py
from django.urls import path
from .views import LogEventView, GetStatsView,analytics_dashboard_page

urlpatterns = [
    path('log/', LogEventView.as_view(), name='log_event'),
    path('stats/', GetStatsView.as_view(), name='get_stats'),
    path('admin-portal/analytics/', analytics_dashboard_page, name='analytics_dashboard'),
    #path('analytics/api/chart-data/', analytics_chart_data, name='analytics_chart_api_endpoint'),
]

