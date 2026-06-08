from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Address
from .serializers import UserSerializer, UserDetailSerializer, UserRegisterSerializer, AddressSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Highly secure ViewSet protecting user account profiles from unauthorized exposure.
    """
    # 🛡️ Limit standard list/retrieve actions to return ONLY the logged-in user's data
    queryset = User.objects.none() 
    serializer_class = UserSerializer
    
    # 🛡️ Default fall-through access policy: completely deny unauthenticated requests
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ensures authenticated users can only view their own record instance.
        """
        if self.request.user and self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'register':
            return UserRegisterSerializer
        elif self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        return UserSerializer

    # 🛡️ Explicitly open ONLY the registration endpoint for public entry
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        # ❌ REMOVED: Raw print statements leaking text passwords into environment stdout logs
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post', 'get'], permission_classes=[permissions.IsAuthenticated])
    def address(self, request):
        user = request.user
        if request.method == 'GET':
            try:
                address = user.address
                serializer = AddressSerializer(address)
                return Response(serializer.data)
            except Address.DoesNotExist:
                return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method == 'POST':
            address, created = Address.objects.get_or_create(user=user)
            serializer = AddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)