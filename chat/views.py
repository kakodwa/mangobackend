from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatMessageSerializer
from products.models import Product

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(Q(buyer=user) | Q(seller=user))

    @action(detail=False, methods=['post'])
    def get_or_create_room(self, request):
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({"detail": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        seller = product.shop.owner
        buyer = request.user

        if buyer == seller:
            return Response({"detail": "You cannot chat with yourself."}, status=status.HTTP_400_BAD_REQUEST)

        room, created = ChatRoom.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            product=product
        )
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all()
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_image(self, request, pk=None):
        room = self.get_object()
        serializer = ChatMessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(room=room, sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)