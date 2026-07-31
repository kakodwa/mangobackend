from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from django.core.mail import send_mail
from django.template.loader import render_to_string


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    # ==========================================
    # HELPER: Send Confirmation Email to Customer
    # ==========================================
    def _send_customer_order_email(self, order):
        customer = order.customer
        if not customer or not customer.email:
            return

        customer_name = customer.first_name or customer.username
        subject = f"MalaTrade: Order Confirmation #{order.id}"

        context = {
            'customer_name': customer_name,
            'order_id': order.id,
            'total_amount': getattr(order, 'total_amount', 0),
        }

        html_message = render_to_string('emails/order_confirmation_customer.html', context)
        plain_message = (
            f"Hello {customer_name},\n\n"
            f"Thank you for your purchase on MalaTrade! Your order #{order.id} has been placed successfully.\n"
            f"Total Amount: ${order.total_amount if hasattr(order, 'total_amount') else ''}\n\n"
            f"We will notify you as soon as your items are prepared and in transit.\n\n"
            f"Best regards,\nMalaTrade Support Team"
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email="orders@malatrade.com",
                recipient_list=[customer.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send customer order email: {e}")

    # ==========================================
    # HELPER: Send New Order Alert Email to Seller
    # ==========================================
    def _send_seller_new_order_email(self, order):
        # Extract seller from order (or order items / shop)
        seller = getattr(order, 'seller', None) or getattr(order, 'shop_owner', None)
        
        # If order items have distinct sellers, extract from items:
        if not seller and hasattr(order, 'items') and order.items.exists():
            first_item = order.items.first()
            seller = getattr(first_item.product, 'seller', None)

        if not seller or not seller.email:
            return

        seller_name = seller.first_name or seller.username
        subject = f"MalaTrade: New Order Received #{order.id}"

        context = {
            'seller_name': seller_name,
            'order_id': order.id,
            'total_amount': getattr(order, 'total_amount', 0),
        }

        html_message = render_to_string('emails/new_order_seller.html', context)
        plain_message = (
            f"Hello {seller_name},\n\n"
            f"You have received a new order #{order.id} on MalaTrade!\n"
            f"Total Order Value: ${order.total_amount if hasattr(order, 'total_amount') else ''}\n\n"
            f"Please log in to your dashboard to process and prepare this order for pickup.\n\n"
            f"Best regards,\nMalaTrade Team"
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
            print(f"Failed to send seller new order email: {e}")

    # ==========================================
    # CREATE ORDER ACTION
    # ==========================================
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        order = serializer.save()

        # 📧 Trigger Emails to Customer & Seller upon successful order creation
        self._send_customer_order_email(order)
        self._send_seller_new_order_email(order)

        return Response(
            OrderSerializer(
                order,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')

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