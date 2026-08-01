import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from utils.sms import send_sms
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Delivery
from .serializers import (
    DeliverySerializer,
    AssignDeliverySerializer,
    DeliveryUpdateSerializer
)

from payments.core.escrow import EscrowService


def generate_customer_code():
    return str(random.randint(100000, 999999))


class DeliveryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    # =========================
    # QUERYSET FILTERING
    # =========================
    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Delivery.objects.all().order_by('-id')

        if getattr(user, 'user_type', None) == "delivery":
            return Delivery.objects.filter(
                delivery_person__user=user
            ).order_by('-id')

        return Delivery.objects.filter(
            seller=user
        ).order_by('-id')

    # =========================
    # SELLER ASSIGN DELIVERY
    # =========================
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        delivery = self.get_object()

        if getattr(request.user, 'user_type', None) != "shop_owner":
            raise PermissionDenied(
                "Only shop owners can assign deliveries"
            )

        serializer = AssignDeliverySerializer(
            delivery,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            DeliverySerializer(delivery).data
        )

    # =========================
    # UPDATE TRACKING
    # =========================
    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        delivery = self.get_object()

        if getattr(request.user, 'user_type', None) not in [
            "delivery",
            "shop_owner"
        ]:
            raise PermissionDenied(
                "Only delivery persons or shop owners can update tracking"
            )

        serializer = DeliveryUpdateSerializer(
            delivery,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            DeliverySerializer(delivery).data
        )

    # =========================
    # GET DELIVERY BY ORDER
    # =========================
    @action(detail=False, methods=['get'])
    def by_order(self, request):
        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response(
                {"error": "order_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        deliveries = Delivery.objects.filter(order_id=order_id)

        if not deliveries.exists():
            return Response(
                {"error": "No deliveries found for this order"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            DeliverySerializer(deliveries, many=True).data
        )

    # =========================
    # OPEN DELIVERY BY CODE
    # =========================
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def open_by_code(self, request):
        code = request.data.get("code")
        
        if not code:
            return Response({"error": "Code required"}, status=status.HTTP_400_BAD_REQUEST)

        delivery = Delivery.objects.filter(delivery_code=code).first()

        if not delivery:
            return Response({"error": "Invalid code"}, status=status.HTTP_404_NOT_FOUND)

        return Response(DeliverySerializer(delivery).data)

    # =========================
    # UPDATE DELIVERY STATUS
    # =========================
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        delivery = self.get_object()

        if (
            getattr(request.user, 'user_type', None) == "delivery"
            and delivery.delivery_person
            and delivery.delivery_person.user != request.user
        ):
            raise PermissionDenied("You are not assigned to this delivery")

        new_status = request.data.get("status")

        allowed_status = [
            "pending",
            "assigned",
            "picked_up",
            "in_transit",
            "failed",
        ]

        if new_status not in allowed_status:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.status = new_status

        # 🎯 TRIGGER: GENERATE CODE + DISPATCH EMAIL/SMS
        if new_status == "in_transit" and not delivery.customer_delivery_code:
            # 1. GENERATE CODE & SAVE
            delivery.customer_delivery_code = generate_customer_code()
            delivery.save()

            print(f"⚡ [CODE GENERATED] Delivery #{delivery.id} code created: {delivery.customer_delivery_code}")

            # 2. RESOLVE CONTACTS
            order = getattr(delivery, 'order', None)
            customer = (
                getattr(order, 'customer', None) or 
                getattr(order, 'user', None) or 
                getattr(delivery, 'customer', None)
            )

            customer_email = getattr(customer, 'email', None) if customer else None
            customer_phone = (
                getattr(delivery, 'customer_phone', None) or 
                (getattr(customer, 'phone_number', None) if customer else None) or
                (getattr(customer, 'phone', None) if customer else None)
            )
            customer_name = getattr(customer, 'first_name', None) or getattr(customer, 'username', 'Customer')
            order_id = str(getattr(order, 'id', delivery.id))
            
            seller = getattr(delivery, 'seller', None)
            shop_name = getattr(getattr(seller, 'shop', None), 'name', 'MalaTrade Shop')

            # 3. DISPATCH SMS
            if customer_phone:
                sms_text = (
                    f"MalaTrade: Your order #{order_id} from {shop_name} is on the way! "
                    f"Verification code: {delivery.customer_delivery_code}. "
                    f"Provide this code to your driver upon receiving your items."
                )
                try:
                    send_sms(customer_phone, sms_text)
                    print(f"[SMS SENT] Sent code {delivery.customer_delivery_code} to {customer_phone}")
                except Exception as e:
                    print(f"[SMS ERROR] Failed sending to {customer_phone}: {e}")

            # 4. DISPATCH EMAIL (CLEAN COPY - PREVENTS SPAM DISCARD)
            if customer_email:
                subject = f"Delivery Update for Order #{order_id}"
                context = {
                    'customer_name': customer_name,
                    'order_id': order_id,
                    'customer_code': delivery.customer_delivery_code,
                    'shop_name': shop_name,
                }
                
                html_message = None
                try:
                    html_message = render_to_string('emails/delivery_in_transit_email.html', context)
                except Exception as tmpl_err:
                    print(f"[Template Warning] Using plain text fallback: {tmpl_err}")

                # Clean text body without financial spam trigger words
                plain_message = (
                    f"Hello {customer_name},\n\n"
                    f"Your order #{order_id} from {shop_name} has been dispatched and is currently in transit.\n\n"
                    f"Verification Code: {delivery.customer_delivery_code}\n\n"
                    f"Please share this verification code with your delivery driver upon receiving and verifying your package.\n\n"
                    f"Thank you for shopping on MalaTrade.\n"
                    f"MalaTrade Support Team"
                )

                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email="support@malatrade.com",
                        recipient_list=[customer_email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    print(f"[EMAIL SENT] Sent code {delivery.customer_delivery_code} to {customer_email}")
                except Exception as e:
                    print(f"[EMAIL ERROR] Email dispatch failed: {e}")
            else:
                print(f"[EMAIL FAILED] Customer email could not be resolved!")

        else:
            delivery.save()

        return Response({
            "message": "Status updated",
            "status": delivery.status,
            "customer_code": (
                delivery.customer_delivery_code
                if new_status == "in_transit"
                else None
            )
        })

    # =========================
    # VERIFY DELIVERY CODE
    # =========================
    @action(detail=True, methods=['post'])
    def verify_delivery(self, request, pk=None):
        delivery = self.get_object()

        if delivery.status == "delivered":
            return Response(
                {"error": "Delivery already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if (
            getattr(request.user, 'user_type', None) == "delivery"
            and delivery.delivery_person
            and delivery.delivery_person.user != request.user
        ):
            raise PermissionDenied("You are not assigned to this delivery")

        code = request.data.get("code")

        if not code:
            return Response(
                {"error": "Delivery code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if code != delivery.customer_delivery_code:
            return Response(
                {"error": "Invalid delivery code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Update Delivery Status
        delivery.status = "delivered"
        delivery.delivered_at = timezone.now()
        delivery.save()

        # 2. Release Escrow
        try:
            EscrowService.release_funds(delivery)
            print(f"[Escrow Release] Released funds for Delivery ID {delivery.id}")
        except Exception as e:
            print(f"[Escrow Release ERROR] Failed for delivery {delivery.id}: {e}")

        # 3. Notify Seller
        seller = getattr(delivery, 'seller', None)
        seller_email = getattr(seller, 'email', None) if seller else None

        if seller_email:
            seller_name = getattr(seller, 'first_name', None) or getattr(seller, 'username', 'Merchant')
            order_id = str(getattr(delivery, 'order_id', delivery.id))

            subject = f"Order #{order_id} Delivery Confirmed"
            context = {
                'seller_name': seller_name,
                'order_id': order_id,
            }

            html_message = None
            try:
                html_message = render_to_string('emails/delivery_completed_seller_email.html', context)
            except Exception:
                pass

            plain_message = (
                f"Hello {seller_name},\n\n"
                f"Order #{order_id} has been delivered successfully.\n"
                f"The customer confirmed delivery with their code, and your payout has been processed.\n\n"
                f"Best regards,\nMalaTrade Support Team"
            )

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email="support@malatrade.com",
                    recipient_list=[seller_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                print(f"[Seller Notification] Sent completion email to {seller_email}")
            except Exception as e:
                print(f"[Seller Notification ERROR] Email failed: {e}")

        return Response({
            "message": "Delivery completed successfully",
            "status": delivery.status
        })