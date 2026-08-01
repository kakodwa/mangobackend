import json
import hmac
import hashlib
import random
import string
import requests
from decimal import Decimal
from collections import defaultdict

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from wallet.models import Wallet, WalletTransaction, Withdrawal, CompanyWallet, CompanyWalletTransaction
from products.models import Product
from events.models import Ticket, TicketItem, EventTicketType
from hospitality.models import Booking
from delivery.models import Delivery

from .models import Payment, PaymentWebhook
from .serializers import PaymentSerializer, PaymentInitiateSerializer
from .services.paychangu_service import PayChanguService
from .services.order_service import OrderService
from .services.refund_service import RefundService
from .handlers.payment_handlers import (
    handle_property_unlock,
    handle_booking,
    handle_ticket,
    handle_wallet_topup,
)


def payment_return_view(request):
    tx_ref = request.GET.get("tx_ref")
    status_val = request.GET.get("status", "pending").lower()
    amount = request.GET.get("amount", "")

    if tx_ref and status_val in ["success", "completed"]:
        try:
            payment = Payment.objects.get(payment_reference=tx_ref)
            # Central fulfillment can be safely called here as well (idempotent)
            fulfill_payment(payment, dict(request.GET), source_name="redirect_return_view")
        except Payment.DoesNotExist:
            print(f"ERROR: Payment object reference '{tx_ref}' not found in database.")

    context = {
        "tx_ref": tx_ref,
        "status": "completed" if status_val in ["success", "completed"] else "failed",
        "amount": amount,
    }
    return render(request, "payments/payment_return.html", context)


def visa_checkout_view(request):
    context = {
        "public_key": getattr(settings, "PAYCHANGU_PUBLIC_KEY", "pub-test-Z2fK1oH31qEvBjtf7FnBhp6CtMZ0vpMW"),
        "tx_ref": request.GET.get("tx_ref"),
        "amount": request.GET.get("amount"),
        "email": request.user.email if request.user and request.user.email else "",
        "first_name": request.user.first_name if request.user else "",
        "last_name": request.user.last_name if request.user else "",
        "callback_url": "https://malatrade.com/api/payments/paychangu_webhook/",
        "return_url": "https://malatrade.com/payment/return/?tx_ref=" + request.GET.get("tx_ref", ""),
        "title": "Payment",
        "description": "Visa Payment",
    }
    return render(request, "payments/visa_checkout.html", context)


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

        # Create base payment record
        payment = serializer.save()

        payment_method = request.data.get("payment_method")
        phone_number = request.data.get("phone_number")

        if phone_number:
            phone_number = phone_number.strip().replace(" ", "")

        # VISA FLOW (SECURE HOSTED LINK)
        if payment_method == "visa_card":
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

            except requests.exceptions.RequestException:
                return Response({
                    "success": False,
                    "message": "Could not establish a connection to the card processor network gateway."
                }, status=status.HTTP_502_BAD_GATEWAY)

            except Exception:
                return Response({
                    "success": False,
                    "message": "Internal gateway communication exception routine framework breakdown."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # MOBILE MONEY FLOW
        service = PayChanguService()
        try:
            result = service.initiate_mobile_money(
                payment,
                phone_number
            )
        except Exception:
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
    @action(
        detail=False,
        methods=['get'],
        url_path=r'status/(?P<reference>[^/.]+)',
        permission_classes=[permissions.IsAuthenticated]
    )
    def payment_status(self, request, reference=None):
        try:
            payment = Payment.objects.get(payment_reference=reference, user=request.user)

            return Response({
                "success": True,
                "payment_reference": payment.payment_reference,
                "status": payment.status,
                "purpose": payment.purpose,
                "amount": payment.amount
            })

        except Payment.DoesNotExist:
            return Response({"success": False, "message": "Payment not found"}, status=404)

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


# ==========================================
# MULTI-VENDOR EMAIL DISPATCH HELPER
# ==========================================
def _send_payment_success_emails(payment):
    """
    Sends payment receipt to Customer and notification to ALL involved 
    Sellers/Merchants once payment is verified as completed.
    Supports single-vendor & multi-vendor order architectures.
    """
    customer = payment.user
    customer_email = getattr(customer, 'email', None)
    customer_name = getattr(customer, 'first_name', None) or getattr(customer, 'username', 'Valued Customer')
    
    amount = payment.amount
    purpose = payment.purpose
    reference = payment.payment_reference
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'payments@malatrade.com')

    # 1. SEND PAYMENT RECEIPT TO CUSTOMER
    if customer_email:
        subject = f"MalaTrade: Payment Receipt [{reference}]"
        context = {
            'customer_name': customer_name,
            'amount': amount,
            'purpose': purpose,
            'reference': reference,
        }
        
        try:
            html_message = render_to_string('emails/payment_success_customer.html', context)
            plain_message = (
                f"Hello {customer_name},\n\n"
                f"Your payment of MWK {amount} for '{purpose}' on MalaTrade has been received successfully!\n"
                f"Reference Code: {reference}\n\n"
                f"Best regards,\nMalaTrade Support Team"
            )

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[customer_email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"[Payment Email] Customer receipt sent to {customer_email}")
        except Exception as e:
            print(f"[Payment Email ERROR] Customer receipt failed: {e}")

    # 2. MULTI-VENDOR ALERT TO ALL INVOLVED SELLERS
    normalized_purpose = str(purpose).lower().strip()
    if any(keyword in normalized_purpose for keyword in ["order", "product", "purchase", "item"]):
        order = getattr(payment, 'order', None)
        
        if order:
            seller_items_map = defaultdict(list)

            # Strategy A: Multi-vendor resolution via OrderItems -> Product -> Seller/Shop Owner
            if hasattr(order, 'items') and order.items.exists():
                for item in order.items.all():
                    product = getattr(item, 'product', None)
                    if not product:
                        continue
                    
                    item_seller = (
                        getattr(product, 'seller', None) or 
                        getattr(product, 'user', None) or 
                        getattr(getattr(product, 'shop', None), 'owner', None)
                    )

                    if item_seller and getattr(item_seller, 'email', None):
                        seller_items_map[item_seller].append(item)

            # Strategy B: Fallback to Direct Order Seller/Shop Owner if items resolution didn't yield sellers
            if not seller_items_map:
                direct_seller = (
                    getattr(order, 'seller', None) or 
                    getattr(order, 'shop_owner', None) or 
                    getattr(getattr(order, 'shop', None), 'owner', None)
                )
                if direct_seller and getattr(direct_seller, 'email', None):
                    all_items = list(order.items.all()) if hasattr(order, 'items') else []
                    seller_items_map[direct_seller] = all_items

            # Dispatch personalized emails to each resolved vendor
            if seller_items_map:
                for seller, items in seller_items_map.items():
                    seller_name = getattr(seller, 'first_name', None) or getattr(seller, 'username', 'Merchant')
                    seller_email = seller.email
                    seller_subject = f"MalaTrade: Payment Secured in Escrow for Order #{order.id}"
                    
                    # Calculate subtotal for vendor's items if price & quantity attributes exist
                    seller_subtotal = sum(
                        getattr(item, 'price', 0) * getattr(item, 'quantity', 1) 
                        for item in items
                    )
                    
                    seller_context = {
                        'seller_name': seller_name,
                        'order_id': order.id,
                        'amount': seller_subtotal if seller_subtotal > 0 else amount,
                        'items': items,
                    }

                    try:
                        seller_html = render_to_string('emails/payment_received_seller.html', seller_context)
                        seller_plain = (
                            f"Hello {seller_name},\n\n"
                            f"Payment for Order #{order.id} has been secured in escrow.\n"
                            f"Please proceed to your dashboard to assign a courier and dispatch the order.\n\n"
                            f"Best regards,\nMalaTrade Support Team"
                        )

                        send_mail(
                            subject=seller_subject,
                            message=seller_plain,
                            from_email=from_email,
                            recipient_list=[seller_email],
                            html_message=seller_html,
                            fail_silently=False,
                        )
                        print(f"[Payment Email] Seller notification sent to {seller_email} for Order #{order.id}")
                    except Exception as e:
                        print(f"[Payment Email ERROR] Failed sending to seller {seller_email}: {e}")
            else:
                print(f"[Payment Email WARNING] Could not resolve any vendor/seller email for Order #{order.id}")
        else:
            print(f"[Payment Email WARNING] No associated Order object attached to Payment reference '{reference}'")
    else:
        print(f"[Payment Email INFO] Purpose '{purpose}' is not classified as an order payment. Skipping seller notification.")


# ==========================================
# CENTRAL FULFILLMENT FUNCTION
# ==========================================
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

        # 📧 5. DISPATCH SUCCESSFUL PAYMENT EMAILS
        _send_payment_success_emails(payment)

        # 6. Record the webhook transaction history logs
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
        withdrawal_id = charge_id.split('-')[-1]
        withdrawal = Withdrawal.objects.get(id=withdrawal_id)
    except (Withdrawal.DoesNotExist, ValueError):
        return JsonResponse({"error": "Withdrawal tracking instance not found"}, status=404)

    if withdrawal.status in ["processed", "rejected"]:
        return JsonResponse({"message": "Withdrawal transaction already finalized."})

    # FAILED PAYOUT -> Refund user wallet
    if status_value not in ["success", "completed"]:
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=withdrawal.user)
            balance_before = wallet.balance
            
            wallet.balance += withdrawal.amount
            wallet.total_withdrawn -= withdrawal.amount
            wallet.save()
            
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

    # SUCCESSFUL PAYOUT
    with transaction.atomic():
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
# WEBHOOK HANDLER
# =========================
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def paychangu_webhook(request):
    data = request.data

    charge_id = data.get("charge_id") or data.get("tx_ref") or data.get("data", {}).get("tx_ref") or ""
    status_value = str(data.get("status", "")).lower()

    if not status_value and isinstance(data.get("data"), dict):
        status_value = str(data.get("data", {}).get("status", "")).lower()

    # ROUTE 1: WITHDRAWAL / CASHOUT
    if str(charge_id).startswith("WD-"):
        return fulfill_withdrawal(charge_id, status_value, data)
    
    # ROUTE 2: INCOMING PAYMENT / DEPOSIT
    else:
        try:
            payment = Payment.objects.get(payment_reference=charge_id)
        except Payment.DoesNotExist:
            return JsonResponse({"error": f"Payment reference context '{charge_id}' not found"}, status=404)

        if payment.status == "completed":
            return JsonResponse({"message": "Already processed natively"})

        if status_value not in ["success", "completed"]:
            payment.status = "failed"
            payment.save()
            return JsonResponse({"success": False, "message": "Payment recorded as failed."})

        # Process successful payment and send emails via central fulfillment
        fulfill_payment(payment, data, source_name="background_webhook")

        return JsonResponse({"success": True, "message": "Webhook processed safely via central handler."})