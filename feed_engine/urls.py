from django.urls import path
from .views import UnifiedSearchView
from .api import (
    HomeFeedAPI,
    ShopFeedAPI,
    EventFeedAPI,
    LodgeFeedAPI,
    PropertyFeedAPI,
)

from django.urls import path


urlpatterns = [
    path("home/", HomeFeedAPI.as_view()),
    path("shops/", ShopFeedAPI.as_view()),
    path("events/", EventFeedAPI.as_view()),
    path("lodges/", LodgeFeedAPI.as_view()),
    path("properties/", PropertyFeedAPI.as_view()),
    path('search/', UnifiedSearchView.as_view(), name='unified-search'),

]