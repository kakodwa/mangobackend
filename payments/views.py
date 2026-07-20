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
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from decimal import Decimal
import random
import string
import requests
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
        "callback_url": "https://malatrade.com/api/payments/paychangu_webhook/",
        "return_url": "https://malatrade.com/payment/return/?tx_ref=" + request.GET.get("tx_ref", ""),
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

        serializer = PaymentInitiateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():


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
        # VISA FLOW (SECURE HOSTED LINK)
        # =========================
        if payment_method == "visa_card":
            import requests
            
            paychangu_url = "https://api.paychangu.com/payment"
            secret_key = getattr(settings, "PAYCHANGU_SECRET_KEY", "")

            if not secret_key:
                print("CRITICAL WARNING: PAYCHANGU_SECRET_KEY is missing from settings.")

            paychangu_payload = {
                "amount": str(payment.amount),
                "currency": "MWK",
                "email": request.user.email if request.user.email else "customer@example.com",
                "first_name": request.user.first_name or request.user.username,
                "last_name": request.user.last_name or "Customer",
                "tx_ref": payment.payment_reference,
                "return_url": "https://malatrade.com/api/payments/webhook/paychangu/",
                "callback_url": (
                    "https://malatrade.com/api/payments/payment/return/"
                    f"?tx_ref={payment.payment_reference}"
                    f"&amount={payment.amount}"
                    f"&status=completed"
                ),
                "customization": {
                    "title": payment.purpose,
                    "description": f"Payment for {payment.purpose}"
                }
            }

            headers = {
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            try:
               
                response = requests.post(
                    paychangu_url,
                    json=paychangu_payload,
                    headers=headers,
                    timeout=15
                )
                
            
                
                res_data = response.json()

                # CHANGED HERE: Accepting 201 Created alongside 200 OK
                if response.status_code in [200, 201] and res_data.get("status") == "success":
                    hosted_checkout_url = res_data.get("data", {}).get("checkout_url")
                    
                    if not hosted_checkout_url:
                        return Response({
                            "success": False,
                            "message": "Gateway initialized but returned an invalid checkout url configuration."
                        }, status=status.HTTP_502_BAD_GATEWAY)

                    return Response({
                        "success": True,
                        "message": "Visa checkout link initialized successfully",
                        "checkout_url": hosted_checkout_url,
                        "payment_reference": payment.payment_reference
                    }, status=status.HTTP_201_CREATED)
                    
                else:
                    return Response({
                        "success": False,
                        "message": res_data.get("message", "PayChangu system rejected request parameters.")
                    }, status=status.HTTP_400_BAD_REQUEST)

            except requests.exceptions.RequestException as req_err:
     
                return Response({
                    "success": False,
                    "message": "Could not establish a connection to the card processor network gateway."
                }, status=status.HTTP_502_BAD_GATEWAY)
                
            except Exception as general_err:
             
                return Response({
                    "success": False,
                    "message": "Internal gateway communication exception routine framework breakdown."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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



def fulfill_payment(payment, gateway_payload, source_name=""):
    """
    A centralized, idempotent function to finalize successful payments
    and trigger downstream business logic handlers.
    """
    if payment.status == "completed":

        return False

    with transaction.atomic():
        # 1. Flip database state to completed
        payment.status = "completed"
        payment.save()


        # 2. Initialize Company Wallet metrics
        company_wallet, _ = CompanyWallet.objects.get_or_create(
            name="Main Company Wallet"
        )

        # 3. Dynamic map structure for background app processors
        HANDLERS = {
            "order_payment": OrderService.process_order,
            "order": OrderService.process_order,
            "property_unlock": handle_property_unlock,
            "booking": handle_booking,
            "ticket": handle_ticket,
            "wallet_topup": handle_wallet_topup,
            "refund": RefundService.refund_order,
        }

        # 4. Fire the assigned backend action handler
        handler = HANDLERS.get(payment.purpose)
        if handler:

            handler(payment, company_wallet)
        else:
            print(f"[Central Fulfillment] Warning: No business handler registered for purpose: {payment.purpose}")

        # 5. Record the webhook transaction history logs smoothly
        PaymentWebhook.objects.create(
            payment=payment,
            webhook_data={
                "source": f"central_fulfillment_{source_name}",
                "raw_payload": gateway_payload
            },
            processed=True
        )
    return True


def fulfill_withdrawal(charge_id, status_value, data):
    """
    Centralized utility function to finalize outbox withdrawals/cashouts
    and securely handle automated user balance refunds if a payout fails.
    """
    try:
        # Extract ID from "WD-MOB-14" or "WD-BNK-14"
        withdrawal_id = charge_id.split('-')[-1]
        withdrawal = Withdrawal.objects.get(id=withdrawal_id)
    except (Withdrawal.DoesNotExist, ValueError):
        return JsonResponse({"error": "Withdrawal tracking instance not found"}, status=404)

    if withdrawal.status in ["processed", "rejected"]:
        return JsonResponse({"message": "Withdrawal transaction already finalized."})

    # =================================================================
    # ❌ CASE A: FAILED PAYOUT (Process Local Refund)
    # =================================================================
    if status_value not in ["success", "completed"]:
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=withdrawal.user)
            balance_before = wallet.balance
            
            # Refund the user's funds locally
            wallet.balance += withdrawal.amount
            wallet.total_withdrawn -= withdrawal.amount
            wallet.save()
            
            # Create historical ledger record of the failure refund
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                source='refund',
                amount=withdrawal.amount,
                balance_before=balance_before,
                balance_after=wallet.balance,
                reference=f"REFUND-{charge_id}",
                description=f"Automated refund due to failed payout drop: {data.get('message', 'Gateway Error')}"
            )
            
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = data.get("message", "PayChangu system disbursement error.")
            withdrawal.save()

            # Ensure you have WithdrawalWebhookLog imported or defined in models
            try:
                from .models import WithdrawalWebhookLog
                WithdrawalWebhookLog.objects.create(
                    withdrawal=withdrawal,
                    webhook_data=data,
                    processed=True
                )
            except ImportError:
                print("Warning: WithdrawalWebhookLog model could not be imported.")

        return JsonResponse({"success": False, "message": "Payout failed. Wallet refunded safely."})

    # =================================================================
    #  CASE B: SUCCESSFUL PAYOUT (Clear Transaction)
    # =================================================================
    with transaction.atomic():
        from django.utils import timezone
        withdrawal.status = "processed"
        withdrawal.processed_at = timezone.now()
        withdrawal.save()

        WalletTransaction.objects.filter(reference=f"WD-REQ-{withdrawal.id}").update(
            description=f"Withdrawal completely cleared by PayChangu to {withdrawal.account_number}"
        )

        try:
            from .models import WithdrawalWebhookLog
            WithdrawalWebhookLog.objects.create(
                withdrawal=withdrawal,
                webhook_data=data,
                processed=True
            )
        except ImportError:
            pass

    return JsonResponse({"success": True, "message": "Withdrawal processed successfully."})


# =========================
# WEBHOOK - USED ALOT BY VISA CARD
# =========================
def payment_return_view(request):
    tx_ref = request.GET.get("tx_ref")
    status_value = request.GET.get("status", "pending").lower()
    amount = request.GET.get("amount", "")



    if tx_ref and status_value in ["success", "completed"]:
        try:
            payment = Payment.objects.get(payment_reference=tx_ref)
       
            # Call our single shared function!
            #fulfill_payment(payment, dict(request.GET), source_name="redirect_return_view")
        except Payment.DoesNotExist:
            print(f"ERROR: Payment object reference '{tx_ref}' not found in database.")

    context = {
        "tx_ref": tx_ref,
        "status": "completed" if status_value in ["success", "completed"] else "failed",
        "amount": amount,
    }
    return render(request, "payments/payment_return.html", context)

# =========================
# WEBHOOK - USED BY MOBILE PA
# =========================
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def paychangu_webhook(request):
    data = request.data


    # Robust tracking ID extractor handles both Mobile Money (charge_id) and Visa (tx_ref)
    charge_id = data.get("charge_id") or data.get("tx_ref") or data.get("data", {}).get("tx_ref") or ""
    status_value = str(data.get("status", "")).lower()

    if not status_value and isinstance(data.get("data"), dict):
        status_value = str(data.get("data", {}).get("status", "")).lower()

    # =================================================================
    # 🔄 ROUTE 1: WITHDRAWAL / CASHOUT
    # =================================================================
    if str(charge_id).startswith("WD-"):
        return fulfill_withdrawal(charge_id, status_value, data)
    # =================================================================
    # 💳 ROUTE 2: INCOMING PAYMENT / DEPOSIT
    # =================================================================
    else:
        try:
            payment = Payment.objects.get(payment_reference=charge_id)
        except Payment.DoesNotExist:
            return JsonResponse({"error": f"Payment reference context '{charge_id}' not found"}, status=404)

        if payment.status == "completed":
            return JsonResponse({"message": "Already processed natively"})

        # --- FAILED PAYMENT ---
        if status_value not in ["success", "completed"]:
            payment.status = "failed"
            payment.save()
            return JsonResponse({"success": False, "message": "Payment recorded as failed."})

        # --- SUCCESS PAYMENT ---
        # Call the exact same single shared function!
        fulfill_payment(payment, data, source_name="background_webhook")

        return JsonResponse({"success": True, "message": "Webhook processed safely via central handler."})