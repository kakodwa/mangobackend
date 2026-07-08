from django.urls import path
from . views import shop_qr_redirect

urlpatterns = [
    path(
        "qr/shop/<int:pk>/",
        shop_qr_redirect,
        name="shop_qr",
    ),
]