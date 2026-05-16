from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import Delivery
from .serializers import (
    DeliverySerializer,
    AssignDeliverySerializer,
    DeliveryUpdateSerializer
)


class DeliveryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    # =========================
    # QUERYSET FILTERING
    # =========================
    def get_queryset(self):
        user = self.request.user

        if user.user_type == "shop_owner":
            return Delivery.objects.filter(
                order__items__product__shop__owner=user
            ).distinct().order_by('-id')

        if user.user_type == "delivery":
            return Delivery.objects.filter(
                delivery_person__user=user
            ).order_by('-id')

        return Delivery.objects.none()

    # =========================
    # SELLER ASSIGN DELIVERY
    # =========================

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):

        delivery = self.get_object()
        if request.user.user_type != "shop_owner":
            raise PermissionDenied("Only shop owners can assign deliveries")
            print("REQUEST DATA:", request.data)

        serializer = AssignDeliverySerializer(
            delivery,
            data=request.data,
            partial=True
            )

        if not serializer.is_valid():
            print("SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(DeliverySerializer(delivery).data)

    # =========================
    # RIDER UPDATE STATUS / TRACKING
    # =========================
    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        delivery = self.get_object()
        user = request.user

        if user.user_type not in ["delivery", "shop_owner"]:
            raise PermissionDenied(
                "Only delivery persons or shop owners can update tracking"
                )

        serializer = DeliveryUpdateSerializer(delivery,
            data=request.data,
            partial=True
            )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DeliverySerializer(delivery).data)

    # =========================
    # GET BY ORDER ID
    # =========================
    @action(detail=False, methods=['get'])
    def by_order(self, request):

        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response({"error": "order_id is required"}, status=400)

        delivery = Delivery.objects.filter(order_id=order_id).first()

        if not delivery:
            return Response({"error": "Delivery not found"}, status=404)

        return Response(DeliverySerializer(delivery).data)

    # =========================
    # OPEN DELIVERY BY CODE (RIDER)
    # =========================
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def open_by_code(self, request):

        code = request.data.get("code")

        if not code:
            return Response({"error": "Code required"}, status=400)

        delivery = Delivery.objects.filter(
            delivery_code=code
        ).first()

        if not delivery:
            return Response({"error": "Invalid code"}, status=404)

        return Response(DeliverySerializer(delivery).data)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def update_status(self, request, pk=None):

        delivery = self.get_object()
        new_status = request.data.get("status")

        allowed_status = [
        "pending",
        "assigned",
        "picked_up",
        "in_transit",
        "delivered",
        "failed"
        ]

        if new_status not in allowed_status:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
                )


        delivery.status = new_status
        delivery.save()

        return Response({
            "message": "Status updated",
            "status": delivery.status
            })