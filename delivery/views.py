from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from utils.sms import send_sms
from django.utils import timezone

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

        # Generate customer verification code
        if (
            new_status == "in_transit"
            and not delivery.customer_delivery_code
        ):
            delivery.customer_delivery_code = (
                generate_customer_code()
            )

            # TODO:
            # Send SMS
            # Send Push Notification
            # Send WhatsApp Message

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

        delivery.status = "delivered"
        delivery.delivered_at = timezone.now()
        delivery.save()


        return Response({
            "message": "Delivery completed successfully",
            "status": delivery.status
        })