from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from utils.sms import send_sms
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Delivery
from .serializers import (
    DeliverySerializer,
    AssignDeliverySerializer,
    DeliveryUpdateSerializer
)

from payments.core.escrow import EscrowService

import random



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

        if user.user_type == "delivery":
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

        if request.user.user_type != "shop_owner":
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

        if request.user.user_type not in [
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

        delivery = Delivery.objects.filter(
            order_id=order_id
        ).first()

        if not delivery:
            return Response(
                {"error": "Delivery not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            DeliverySerializer(delivery).data
        )

    # =========================
    # OPEN DELIVERY BY CODE
    # =========================
    @action(detail=False,methods=['post'],permission_classes=[AllowAny],authentication_classes=[])
    def open_by_code(self, request):
        code = request.data.get("code")
        
        if not code:
            return Response({"error": "Code required"},status=status.HTTP_400_BAD_REQUEST)

        delivery = Delivery.objects.filter(delivery_code=code).first()

        if not delivery:
            return Response({"error": "Invalid code"},status=status.HTTP_404_NOT_FOUND)

        return Response(DeliverySerializer(delivery).data)
    # =========================
    # UPDATE DELIVERY STATUS
    # =========================
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        delivery = self.get_object()

        if (
            request.user.user_type == "delivery"
            and delivery.delivery_person
            and delivery.delivery_person.user != request.user
        ):
            raise PermissionDenied(
                "You are not assigned to this delivery"
            )

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

        # Generate customer verification code and notify customer when status switches to in_transit
        if (
            new_status == "in_transit"
            and not delivery.customer_delivery_code
        ):
            delivery.customer_delivery_code = generate_customer_code()
            delivery.save()

            # Extract customer contact details (adjust attribute access based on your Order/User relationships)
            customer = getattr(delivery.order, 'customer', None) or getattr(delivery, 'customer', None)
            customer_email = getattr(customer, 'email', None) if customer else None
            customer_phone = getattr(delivery, 'customer_phone', None) or (getattr(customer, 'phone_number', None) if customer else None)
            customer_name = getattr(customer, 'first_name', None) or getattr(customer, 'username', 'Valued Customer')
            order_id = str(delivery.order_id if hasattr(delivery, 'order_id') else delivery.id)

            # 1. Send SMS via utils.sms
            if customer_phone:
                sms_text = (
                    f"MalaTrade Alert: Your package for order #{order_id} is in transit! "
                    f"Your secret delivery code is {delivery.customer_delivery_code}. "
                    f"Share this code with the seller/courier ONLY after inspecting your package to release funds."
                )
                try:
                    send_sms(customer_phone, sms_text)
                except Exception as e:
                    # Log error in production so SMS failure doesn't block status update
                    print(f"SMS dispatch failed: {e}")

            # 2. Send HTML Email
            if customer_email:
                subject = f"MalaTrade: Your Order #{order_id} is In Transit"
                context = {
                    'customer_name': customer_name,
                    'order_id': order_id,
                    'customer_code': delivery.customer_delivery_code,
                }
                
                html_message = render_to_string('emails/delivery_in_transit_email.html', context)
                plain_message = (
                    f"Hello {customer_name},\n\n"
                    f"Your order #{order_id} is now in transit!\n"
                    f"Your confidential delivery code is: {delivery.customer_delivery_code}\n\n"
                    f"IMPORTANT:\n"
                    f"- Keep this code secret until you receive and inspect your items.\n"
                    f"- Sharing this code with your courier releases the escrow payment to the seller.\n"
                    f"- If you receive the item but forget to provide the code, funds will automatically release after 2 days (48 hrs) if no dispute is opened.\n\n"
                    f"Best regards,\nMalaTrade Support Team"
                )

                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email="orders@malatrade.com",
                        recipient_list=[customer_email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Email dispatch failed: {e}")

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
            request.user.user_type == "delivery"
            and delivery.delivery_person
            and delivery.delivery_person.user != request.user
        ):
            raise PermissionDenied(
                "You are not assigned to this delivery"
            )

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

        # 2. Release Funds from Escrow
        try:
            # Pass delivery or delivery.order depending on your EscrowService signature
            EscrowService.release_funds(delivery)
        except Exception as e:
            print(f"Escrow release failed for delivery {delivery.id}: {e}")

        # 3. Send Notification Email to Seller
        seller = delivery.seller  # Adjust attribute if seller is linked differently
        if seller and seller.email:
            seller_name = seller.first_name or seller.username
            order_id = str(delivery.order_id if hasattr(delivery, 'order_id') else delivery.id)

            subject = f"MalaTrade: Payment Released for Order #{order_id}"
            context = {
                'seller_name': seller_name,
                'order_id': order_id,
            }

            html_message = render_to_string('emails/delivery_completed_seller_email.html', context)
            plain_message = (
                f"Hello {seller_name},\n\n"
                f"Order #{order_id} has been delivered successfully!\n"
                f"The customer verified receipt with their delivery code, and the escrow funds have been released to your account.\n\n"
                f"Best regards,\nMalaTrade Support Team"
            )

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email="orders@malatrade.com",
                    recipient_list=[seller.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Seller email notification failed: {e}")

        return Response({
            "message": "Delivery completed successfully and funds released from escrow",
            "status": delivery.status
        })