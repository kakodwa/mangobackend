from rest_framework.decorators import action, api_view
import json
import hmac
import hashlib
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from wallet.models import Wallet, WalletTransaction, Withdrawal,CompanyWallet,CompanyWalletTransaction
from .paychangu_service import PayChanguService
from .models import Payment, PaymentWebhook
from delivery.models import Delivery
from decimal import Decimal
import random
import string
from .serializers import PaymentSerializer, PaymentInitiateSerializer

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
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def initiate_payment(self, request):

        print("REQUEST PAYMENT DATA:", request.data)

        serializer = PaymentInitiateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            print("PAYMENT ERRORS:", serializer.errors)

            first_error = None
            for field, errors in serializer.errors.items():
                first_error = errors[0]
                break

            return Response({
                "success": False,
                "message": first_error or "Invalid input data"
                }, status=status.HTTP_400_BAD_REQUEST)

        # 1. CREATE PAYMENT FIRST
        payment = serializer.save()

        # 2. GET DATA FROM REQUEST (IMPORTANT FIX)
        phone_number = request.data.get("phone_number")
        payment_method = request.data.get("payment_method")

        # clean phone
        if phone_number:
            phone_number = phone_number.strip().replace(" ", "")

        # 3. CALL PAYCHANGU SERVICE
        service = PayChanguService()

        try:
            if payment_method == "visa_card":
                result = service.initiate_card_payment(
                    payment,
                    redirect_url="https://yourdomain.com/payment/success/"
                )
            else:
                result = service.initiate_mobile_money(
                    payment,
                    phone_number 
                )

        except Exception as e:
            return Response({
                "success": False,
                "message": "Server error. Please try again later."
                }, status=500)

        # 4. CHECK RESPONSE
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
@api_view(['POST'])
def paychangu_webhook(request):

    print("WEBHOOK HIT")

    data = request.data
    print("RAW WEBHOOK DATA:", data)

    transaction_id = data.get("charge_id")
    status_value = data.get("status")

    try:
        payment = Payment.objects.get(
            payment_reference=transaction_id
        )

        # Prevent double execution
        if payment.status == "completed":
            return JsonResponse({
                "message": "Already processed"
            })

        # ===============================
        # PAYMENT SUCCESS
        # ===============================
        if status_value in ["success", "completed"]:

            payment.status = "completed"
            payment.save()

            # ==========================================
            # GET COMPANY WALLET
            # ==========================================
            company_wallet, _ = CompanyWallet.objects.get_or_create(
                name="Main Company Wallet"
            )

            # --------------------------------
            # PROPERTY UNLOCK PAYMENT
            # --------------------------------
            if payment.purpose == "property_unlock":

                unlock = payment.property_unlock

                unlock.is_unlocked = True
                unlock.save()

                owner = unlock.property.owner

                owner_wallet, _ = Wallet.objects.get_or_create(
                    user=owner
                )

                # 🔥 COMMISSION RATE
                commission_rate = Decimal("15.00")

                owner_amount = payment.amount * (
                    Decimal("1") - (
                        commission_rate / Decimal("100")
                    )
                )

                company_amount = payment.amount * (
                    commission_rate / Decimal("100")
                )

                # =====================================
                # OWNER WALLET
                # =====================================
                owner_before = owner_wallet.balance

                owner_wallet.balance += owner_amount
                owner_wallet.total_earnings += owner_amount
                owner_wallet.save()

                WalletTransaction.objects.create(
                    wallet=owner_wallet,
                    transaction_type="credit",
                    source="property_unlock",
                    amount=owner_amount,
                    transaction_rate=commission_rate,
                    balance_before=owner_before,
                    balance_after=owner_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Property unlock #{unlock.id}"
                )

                # =====================================
                # COMPANY WALLET
                # =====================================
                company_before = company_wallet.balance

                company_wallet.balance += company_amount
                company_wallet.total_earnings += company_amount
                company_wallet.save()

                CompanyWalletTransaction.objects.create(
                    wallet=company_wallet,
                    transaction_type="credit",
                    source="property_unlock_commission",
                    amount=company_amount,
                    transaction_rate=commission_rate,
                    balance_before=company_before,
                    balance_after=company_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Commission from property unlock #{unlock.id}"
                )

            # --------------------------------
            # ORDER PAYMENT
            # --------------------------------
            elif payment.purpose == "order":

                order = payment.order

                order.status = "confirmed"
                order.save()

          
                Delivery.objects.create(
                    order=order,
                    status="pending",
                    customer_latitude=order.delivery_latitude,
                    customer_longitude=order.delivery_longitude,
                    delivery_address = order.delivery_address,
                    delivery_phone_number = order.delivery_phone_number,
                    delivery_code=generate_code()
                    )

                seller = order.items.first().product.shop.owner

                seller_wallet, _ = Wallet.objects.get_or_create(
                    user=seller
                )

                # 🔥 COMMISSION RATE
                commission_rate = Decimal("10.00")

                seller_amount = order.total_amount * (
                    Decimal("1") - (
                        commission_rate / Decimal("100")
                    )
                )

                company_amount = order.total_amount * (
                    commission_rate / Decimal("100")
                )

                # =====================================
                # SELLER WALLET
                # =====================================
                seller_before = seller_wallet.balance

                seller_wallet.balance += seller_amount
                seller_wallet.total_earnings += seller_amount
                seller_wallet.save()

                WalletTransaction.objects.create(
                    wallet=seller_wallet,
                    transaction_type="credit",
                    source="order_payment",
                    amount=seller_amount,
                    transaction_rate=commission_rate,
                    balance_before=seller_before,
                    balance_after=seller_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Order {order.order_number}"
                )

                # =====================================
                # COMPANY WALLET
                # =====================================
                company_before = company_wallet.balance

                company_wallet.balance += company_amount
                company_wallet.total_earnings += company_amount
                company_wallet.save()

                CompanyWalletTransaction.objects.create(
                    wallet=company_wallet,
                    transaction_type="credit",
                    source="order_commission",
                    amount=company_amount,
                    transaction_rate=commission_rate,
                    balance_before=company_before,
                    balance_after=company_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Commission from order {order.order_number}"
                )

            # --------------------------------
            # WALLET TOPUP
            # --------------------------------
            elif payment.purpose == "wallet_topup":

                wallet, _ = Wallet.objects.get_or_create(
                    user=payment.user
                )

                balance_before = wallet.balance

                wallet.balance += payment.amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type="credit",
                    source="bonus",
                    amount=payment.amount,
                    transaction_rate=Decimal("0.00"),
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    reference=payment.payment_reference,
                    description="Wallet Topup"
                )

        # ===============================
        # PAYMENT FAILED
        # ===============================
        else:

            payment.status = "failed"
            payment.save()

        PaymentWebhook.objects.create(
            payment=payment,
            webhook_data=data,
            processed=True
        )

        return JsonResponse({
            "success": True
        })

    except Payment.DoesNotExist:

        return JsonResponse({
            "error": "Payment not found"
        }, status=404)

# =========================
# SIGNATURE VERIFY
# =========================
def verify_paychangu_signature(data):
    api_key = settings.PAYCHANGU_API_KEY
    signature = data.get('signature')

    signature_string = f"{data.get('amount')}{data.get('currency')}{api_key}"
    expected_signature = hashlib.sha256(signature_string.encode()).hexdigest()

    return signature == expected_signature