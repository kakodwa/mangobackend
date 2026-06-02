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


            elif payment.purpose == "booking":
                
                booking = payment.booking
                if not booking:
                    return JsonResponse({
                        "error": "Booking not linked to payment"
                        }, status=400)

                booking.booking_status = "confirmed"
                booking.payment_status = 'paid'
                booking.save()
    

                owner = booking.room.lodge.owner
                owner_wallet, _ = Wallet.objects.get_or_create(user=owner)

                commission_rate = Decimal("10.00")

                owner_amount = payment.amount * (Decimal("1") - commission_rate / Decimal("100"))
                company_amount = payment.amount * (commission_rate / Decimal("100"))
                owner_before = owner_wallet.balance

                owner_wallet.balance += owner_amount
                owner_wallet.total_earnings += owner_amount
                owner_wallet.save()

                WalletTransaction.objects.create(
                    wallet=owner_wallet,
                    transaction_type="credit",
                    source="booking_payment",
                    amount=owner_amount,
                    transaction_rate=commission_rate,
                    balance_before=owner_before,
                    balance_after=owner_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Booking #{booking.id}"
                    )

            # --------------------------------
            # ORDER PAYMENT
            # --------------------------------
            elif payment.purpose == "order":

                order = payment.order

                # =====================================
                # PRODUCT STOCK DEDUCTION
                # =====================================
                for item in order.items.select_related("product"):
                    updated = Product.objects.filter(
                        id=item.product.id,
                        stock__gte=item.quantity
                        ).update(
                        stock=F("stock") - item.quantity
                        )

                    if updated == 0:
                        raise Exception(f"Not enough stock for {item.product.name}")

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


            elif payment.purpose == "ticket":
                ticket = payment.ticket_purchase

                if not ticket:
                    return JsonResponse({"error": "Ticket not linked to payment"}, status=400)
                
                # idempotency guards
                if ticket.payment_status == "paid":
                    return JsonResponse({"message": "Ticket already paid"})

                if PaymentWebhook.objects.filter(payment=payment, processed=True).exists():
                    return JsonResponse({"message": "Already processed"})

                event = ticket.event
                

                 # =====================================
                 # ATOMIC STOCK + PAYMENT FINALIZATION
                 # =====================================

                with transaction.atomic():
                     # STEP 1: deduct stock
                    for item in ticket.items.select_related("ticket_type"):

                        updated = EventTicketType.objects.filter(
                            id=item.ticket_type.id,
                            available_seats__gte=item.quantity
                            ).update(
                            available_seats=F("available_seats") - item.quantity)

                        if updated == 0:
                            raise Exception(f"Not enough seats for {item.ticket_type.name}")
                    

                    # STEP 2: mark ticket paid ONLY AFTER success
                    ticket.payment_status = "paid"
                    ticket.save()

                

                # =====================================
                # WALLET LOGIC (outside atomic block OK)
                # =====================================
                organizer = event.organizer
                organizer_wallet, _ = Wallet.objects.get_or_create(user=organizer)


                commission_rate = Decimal("10.00")
                organizer_amount = payment.amount * (Decimal("1") - commission_rate / Decimal("100"))
                company_amount = payment.amount * (commission_rate / Decimal("100"))

                before_balance = organizer_wallet.balance
                organizer_wallet.balance += organizer_amount
                organizer_wallet.total_earnings += organizer_amount
                organizer_wallet.save()


                WalletTransaction.objects.create(
                    wallet=organizer_wallet,
                    transaction_type="credit",
                    source="ticket_payment",
                    amount=organizer_amount,
                    transaction_rate=commission_rate,
                    balance_before=before_balance,
                    balance_after=organizer_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Ticket sale - {event.title}"
                    )

                company_before = company_wallet.balance
                company_wallet.balance += company_amount
                company_wallet.total_earnings += company_amount
                company_wallet.save()


                CompanyWalletTransaction.objects.create(
                    wallet=company_wallet,
                    transaction_type="credit",
                    source="ticket_commission",
                    amount=company_amount,
                    transaction_rate=commission_rate,
                    balance_before=company_before,
                    balance_after=company_wallet.balance,
                    reference=payment.payment_reference,
                    description=f"Commission from ticket {event.title}"
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