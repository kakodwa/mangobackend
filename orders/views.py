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

import logging
logger = logging.getLogger(__name__)


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
        customer = getattr(order, 'customer', None)
        if not customer or not getattr(customer, 'email', None):
            logger.warning(f"No valid customer email found for Order #{order.id}")
            return

        customer_name = getattr(customer, 'first_name', '') or customer.username
        subject = f"MalaTrade: Order Confirmation #{order.id}"

        context = {
            'customer_name': customer_name,
            'order_id': order.id,
            'total_amount': getattr(order, 'total_amount', 0),
        }

        try:
            html_message = render_to_string('emails/order_confirmation_customer.html', context)
        except Exception as e:
            logger.warning(f"Failed rendering customer HTML email template: {e}")
            html_message = None

        plain_message = (
            f"Hello {customer_name},\n\n"
            f"Thank you for your purchase on MalaTrade! Your order #{order.id} has been placed successfully.\n"
            f"Total Amount: MWK {getattr(order, 'total_amount', 0)}\n\n"
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
            logger.info(f"Customer confirmation email sent to {customer.email} for Order #{order.id}")
        except Exception as e:
            logger.error(f"Failed to send customer order email for Order #{order.id}: {e}")

    # ==========================================
    # HELPER: Send New Order Alert Email to All Related Sellers / Shops
    # ==========================================
    def _send_seller_new_order_email(self, order):
        seller_emails = set()

        # Strategy 1: Check Order Items -> Product -> Shop -> Owner / Email
        if hasattr(order, 'items') and order.items.exists():
            for item in order.items.all():
                product = getattr(item, 'product', None)
                if product:
                    shop = getattr(product, 'shop', None) or getattr(product, 'store', None)
                    if shop:
                        owner = getattr(shop, 'owner', None)
                        if owner and getattr(owner, 'email', None):
                            seller_emails.add((owner.email, getattr(owner, 'first_name', '') or owner.username))
                        elif getattr(shop, 'email', None):
                            seller_emails.add((shop.email, shop.name))
                        continue

                    # Direct seller attached to product
                    direct_seller = (
                        getattr(product, 'seller', None) or 
                        getattr(product, 'user', None) or 
                        getattr(product, 'vendor', None)
                    )
                    if direct_seller and getattr(direct_seller, 'email', None):
                        seller_emails.add((
                            direct_seller.email, 
                            getattr(direct_seller, 'first_name', '') or direct_seller.username
                        ))

        # Strategy 2: Check Sub-Orders (seller_orders)
        if not seller_emails and hasattr(order, 'seller_orders') and order.seller_orders.exists():
            for seller_order in order.seller_orders.all():
                shop = getattr(seller_order, 'shop', None) or getattr(seller_order, 'store', None)
                if shop:
                    owner = getattr(shop, 'owner', None)
                    if owner and getattr(owner, 'email', None):
                        seller_emails.add((owner.email, getattr(owner, 'first_name', '') or owner.username))
                    elif getattr(shop, 'email', None):
                        seller_emails.add((shop.email, shop.name))

        # Strategy 3: Check Direct Shop on Order model
        if not seller_emails:
            order_shop = getattr(order, 'shop', None)
            if order_shop:
                owner = getattr(order_shop, 'owner', None)
                if owner and getattr(owner, 'email', None):
                    seller_emails.add((owner.email, getattr(owner, 'first_name', '') or owner.username))
                elif getattr(order_shop, 'email', None):
                    seller_emails.add((order_shop.email, order_shop.name))

        if not seller_emails:
            logger.warning(f"No sellers or shop owners identified to receive order email alert for Order #{order.id}")
            return

        # Send email alert to every unique seller/shop email found
        for email, name in seller_emails:
            subject = f"MalaTrade: New Order Received #{order.id}"

            context = {
                'seller_name': name,
                'order_id': order.id,
                'total_amount': getattr(order, 'total_amount', 0),
            }

            try:
                html_message = render_to_string('emails/new_order_seller.html', context)
            except Exception as e:
                logger.warning(f"Failed rendering seller HTML email template: {e}")
                html_message = None

            plain_message = (
                f"Hello {name},\n\n"
                f"You have received a new order #{order.id} on MalaTrade!\n"
                f"Total Order Value: MWK {getattr(order, 'total_amount', 0)}\n\n"
                f"Please log in to your dashboard to process and prepare this order for pickup.\n\n"
                f"Best regards,\nMalaTrade Team"
            )

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email="orders@malatrade.com",
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Seller alert email sent to {email} for Order #{order.id}")
            except Exception as e:
                logger.error(f"Failed to send seller email to {email} for Order #{order.id}: {e}")

    # ==========================================
    # CREATE ORDER ACTION
    # ==========================================
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.save()

        # 🔑 Force Django to re-read items created within transaction
        order.refresh_from_db()

        # 📧 Trigger Emails to Customer & Sellers upon successful order creation
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