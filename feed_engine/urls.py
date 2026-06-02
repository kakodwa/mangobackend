from django.urls import path
from .api import (
    HomeFeedAPI,
    ShopFeedAPI,
    EventFeedAPI,
    LodgeFeedAPI,
    PropertyFeedAPI,
)

urlpatterns = [
    path("home/", HomeFeedAPI.as_view()),
    path("shops/", ShopFeedAPI.as_view()),
    path("events/", EventFeedAPI.as_view()),
    path("lodges/", LodgeFeedAPI.as_view()),
    path("properties/", PropertyFeedAPI.as_view()),
]