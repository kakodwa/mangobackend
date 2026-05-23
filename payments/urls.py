from django.urls import path
from .views import payment_return_view,visa_checkout_view

urlpatterns = [
    path("payment/return/", payment_return_view, name="payment-return"),
    path("payment/visa/", visa_checkout_view),
]