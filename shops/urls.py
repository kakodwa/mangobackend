from django.urls import path
from . views import shop_qr_redirect,download_app_view

urlpatterns = [
    path(
        "qr/shop/<int:pk>/",
        shop_qr_redirect,
        name="shop_qr",
    ),
    path(
        "app/download/",
        download_app_view,
        name="download_app",
    ),
]