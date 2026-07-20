from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']  #Removed shop
    ordering_fields = ['created_at', 'total_amount']


    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(customer=user)


    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):

        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
            )

        if not serializer.is_valid():

            return Response(serializer.errors, status=400)

        order = serializer.save()

        return Response(
            OrderSerializer(
                order,
                context={'request': request}
                ).data,
            status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')

        # Only admin OR future logic (you can improve later)
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response(OrderSerializer(order).data)

        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = self.get_queryset().filter(customer=request.user)
        return Response(OrderSerializer(orders, many=True).data)


    def get_delivery(self, obj):
        delivery = getattr(obj, "delivery", None)

        if not delivery:
            return None

        return {
        "id": delivery.id,
        "status": delivery.status,
        "delivery_code": delivery.delivery_code,
        "pickup_latitude": delivery.pickup_latitude,
        "pickup_longitude": delivery.pickup_longitude,
        "customer_latitude": delivery.customer_latitude,
        "customer_longitude": delivery.customer_longitude,
        "delivery_person": DeliveryPersonSerializer(delivery.delivery_person).data if delivery.delivery_person else None,
        }