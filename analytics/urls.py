# analytics/urls.py
from django.urls import path
from .views import LogEventView, GetStatsView,track_and_download

urlpatterns = [
    path('log/', LogEventView.as_view(), name='log_event'),
    path('stats/', GetStatsView.as_view(), name='get_stats'),
    path('download-apk/', track_and_download, name='track_and_download'),

]