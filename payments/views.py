from rest_framework.decorators import action, api_view
import json
import hmac
import hashlib
from collections import defaultdict
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from wallet.models import Wallet, WalletTransaction, Withdrawal,CompanyWallet,CompanyWalletTransaction
from .services.paychangu_service import PayChanguService
from .services.order_service import OrderService
from .services.refund_service import RefundService
from django.db.models import F
from .models import Payment, PaymentWebhook
from products.models import Product
from django.db import transaction
from events.models import Ticket,TicketItem,EventTicketType
from hospitality.models import Booking
from delivery.models import Delivery
from decimal import Decimal
import random
import string
from .handlers.payment_handlers import (
    handle_property_unlock,
    handle_booking,
    handle_ticket,
    handle_wallet_topup,
)
from .serializers import PaymentSerializer, PaymentInitiateSerializer
from django.shortcuts import render


def payment_return_view(request):
    tx_ref = request.GET.get("tx_ref")
    status = request.GET.get("status", "pending")
    amount = request.GET.get("amount", "")

    context = {
        "tx_ref": tx_ref,
        "status": status,
        "amount": amount,
    }

    return render(request, "payments/payment_return.html", context)


def visa_checkout_view(request):

    context = {
        "public_key": "pub-test-Z2fK1oH31qEvBjtf7FnBhp6CtMZ0vpMW",
        "tx_ref": request.GET.get("tx_ref"),
        "amount": request.GET.get("amount"),
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "callback_url": "https://yourdomain.com/api/payments/paychangu_webhook/",
        "return_url": "https://yourdomain.com/payment/return/?tx_ref=" + request.GET.get("tx_ref", ""),
        "title": "Payment",
        "description": "Visa Payment",
    }

    return render(request, "payments/visa_checkout.html", context)

#Code used by assigned delivery person
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    # =========================
    # INITIATE PAYMENT
    # =========================
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def initiate_payment(self, request):

        print("REQUEST PAYMENT DATA:", request.data)

        serializer = PaymentInitiateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():

            print("PAYMENT ERRORS:", serializer.errors)

            first_error = None
            for _, errors in serializer.errors.items():
                first_error = errors[0]
                break

            return Response({
                "success": False,
                "message": first_error or "Invalid input data"
            }, status=status.HTTP_400_BAD_REQUEST)

        # =========================
        # CREATE PAYMENT FIRST
        # =========================
        payment = serializer.save()

        payment_method = request.data.get("payment_method")
        phone_number = request.data.get("phone_number")

        if phone_number:
            phone_number = phone_number.strip().replace(" ", "")

        # =========================
        # VISA FLOW (NO PAYCHANGU CALL)
        # =========================
        if payment_method == "visa_card":

            visa_data = {
                "public_key": "pub-test-Z2fK1oH31qEvBjtf7FnBhp6CtMZ0vpMW",
                "tx_ref": payment.payment_reference,
                "amount": str(payment.amount),
                "currency": "MWK",
                "email": request.user.email,
                "first_name": request.user.first_name or request.user.username,
                "last_name": request.user.last_name or "",
                "callback_url": "https://yourdomain.com/payments/paychangu_callback/",
                 "return_url": (
                    "http://127.0.0.1:8000/api/payments/payment/return/"
                    f"?tx_ref={payment.payment_reference}"
                    f"&amount={payment.amount}"
                    f"&status=completed"
                    ),
                "title": payment.purpose,
                "description": f"Payment for {payment.purpose}",
            }

            return Response({
                "success": True,
                "message": "Visa payment initialized",
                "payment_id": payment.id,
                "payment_reference": payment.payment_reference,
                "visa_payment": visa_data
            }, status=status.HTTP_201_CREATED)

        # =========================
        # MOBILE MONEY FLOW
        # =========================
        service = PayChanguService()

        try:
            result = service.initiate_mobile_money(
                payment,
                phone_number
            )

        except Exception as e:
            return Response({
                "success": False,
                "message": "Server error. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not result.get("success"):
            return Response({
                "success": False,
                "message": result.get("message", "Payment failed")
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Payment initiated successfully",
            "payment_id": payment.id,
            "payment_reference": payment.payment_reference,
            "paychangu": result["data"]
        }, status=status.HTTP_201_CREATED)

    # =========================
    # PAYMENT STATUS (POLLING)
    # =========================
    @action(detail=False,methods=['get'],url_path=r'status/(?P<reference>[^/.]+)',permission_classes=[permissions.IsAuthenticated])
    def payment_status(self, request, reference=None):

        print("REQUEST STATUS DATA:", request.data)

        try:
            payment = Payment.objects.get(payment_reference=reference,user=request.user)

            return Response({
                "success": True,
                "payment_reference": payment.payment_reference,
                "status": payment.status,
                "purpose": payment.purpose,
                "amount": payment.amount
                })

        except Payment.DoesNotExist:
            return Response({"success": False,"message": "Payment not found"}, status=404)

    # =========================
    # LIST USER PAYMENTS
    # =========================
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_payments(self, request):
        payments = self.get_queryset()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    
    # =========================
    # CHECK PAYMENT STATUS
    # =========================
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def check_payment_status(self, request):


        reference = request.query_params.get("reference")

        if not reference:
            return Response({
                "success": False,
                "message": "Payment reference required"
                }, status=400)

        try:
            payment = Payment.objects.get(
                payment_reference=reference,
                user=request.user
                )

            return Response({
                "success": True,
                "payment_reference": payment.payment_reference,
                "status": payment.status,
                "purpose": payment.purpose
                })

        except Payment.DoesNotExist:
            return Response({
                "success": False,
                "message": "Payment not found"
                }, status=404)


# =========================
# WEBHOOK
# =========================

@csrf_exempt
@api_view(["POST"])
def paychangu_webhook(request):

    data = request.data

    try:
        payment = Payment.objects.get(
            payment_reference=data.get("charge_id")
        )

    except Payment.DoesNotExist:
        return JsonResponse({"error": "Payment not found"}, status=404)

    # -------------------------
    # IDENTITY CHECK (IDEMPOTENCY)
    # -------------------------
    if payment.status == "completed":
        return JsonResponse({"message": "Already processed"})

    # -------------------------
    # FAILED PAYMENT
    # -------------------------
    if data.get("status") not in ["success", "completed"]:
        payment.status = "failed"
        payment.save()

        PaymentWebhook.objects.create(
            payment=payment,
            webhook_data=data,
            processed=True
        )

        return JsonResponse({"success": False})

    # -------------------------
    # SUCCESS PAYMENT
    # -------------------------
    with transaction.atomic():

        payment.status = "completed"
        payment.save()

        company_wallet, _ = CompanyWallet.objects.get_or_create(
            name="Main Company Wallet"
        )


        HANDLERS = {
            "order":OrderService.process_order,               # now escrow-based
            "property_unlock": handle_property_unlock,
            "booking": handle_booking,
            "ticket": handle_ticket,
            "wallet_topup": handle_wallet_topup,
            "refund":RefundService.refund_order,
        }

        handler = HANDLERS.get(payment.purpose)

        if handler:
            handler(payment, company_wallet)

        PaymentWebhook.objects.create(
            payment=payment,
            webhook_data=data,
            processed=True
        )

    return JsonResponse({"success": True})


'''@csrf_exempt
@api_view(["POST"])
def paychangu_webhook(request):
    data = request.data

    transaction_id = data.get("charge_id")
    status_value = data.get("status")

    try:
        payment = Payment.objects.get(
            payment_reference=transaction_id
        )

        if payment.status == "completed":
            return JsonResponse({"message": "Already processed"})

        if status_value not in ["success", "completed"]:
            payment.status = "failed"
            payment.save()

            PaymentWebhook.objects.create(
                payment=payment,
                webhook_data=data,
                processed=True
            )

            return JsonResponse({"success": False})

        with transaction.atomic():

            payment.status = "completed"
            payment.save()

            company_wallet, _ = CompanyWallet.objects.get_or_create(
                name="Main Company Wallet"
            )

            if payment.purpose == "property_unlock":
                handle_property_unlock(
                    payment,
                    company_wallet
                )

            elif payment.purpose == "booking":
                handle_booking(
                    payment,
                    company_wallet
                )

            elif payment.purpose == "order":
                handle_order(
                    payment,
                    company_wallet
                )

            elif payment.purpose == "ticket":
                handle_ticket(
                    payment,
                    company_wallet
                )

            elif payment.purpose == "wallet_topup":
                handle_wallet_topup(
                    payment
                )

            PaymentWebhook.objects.create(
                payment=payment,
                webhook_data=data,
                processed=True
            )

        return JsonResponse({"success": True})

    except Payment.DoesNotExist:
        return JsonResponse(
            {"error": "Payment not found"},
            status=404
        )'''


