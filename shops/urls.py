from django.urls import path

urlpatterns = [
    path(
        "qr/shop/<int:pk>/",
        shop_qr_redirect,
        name="shop_qr",
    ),
]