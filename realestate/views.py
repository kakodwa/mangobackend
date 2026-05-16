from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyUnlock
from django.db.models import Q
from .serializers import PropertySerializer, PropertyCreateUpdateSerializer, PropertyUnlockSerializer
from payments.models import Payment


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.filter(is_publicly_visible=True)
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'status', 'city', 'district']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['price', 'created_at', 'view_count']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == 'property_owner':
            return Property.objects.filter(owner=user)
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

        except Exception as e:
            print("❌ PROPERTY CREATE VALIDATION ERROR:")
            print(serializer.errors)
            print("RAW EXCEPTION:", e)

            raise

        print("✅ VALID DATA:", serializer.validated_data)
        self.perform_create(serializer)

        return Response(serializer.data, status=201)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def related(self, request, pk=None):

        property_obj = self.get_object()

        related_qs = Property.objects.filter(
            Q(property_type=property_obj.property_type) |
            Q(district=property_obj.district) |
            Q(city=property_obj.city),
            is_publicly_visible=True).exclude(id=property_obj.id)


        print(related_qs)

        if not related_qs.exists():
            related_qs = Property.objects.filter(
                is_publicly_visible=True
                ).exclude(id=property_obj.id)[:10]

        serializer = PropertySerializer(
            related_qs,
            many=True,
            context={'request': request}
            )
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateUpdateSerializer
        return PropertySerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unlock(self, request, pk=None):
        property_obj = self.get_object()

        if PropertyUnlock.objects.filter(property=property_obj,customer=request.user,is_unlocked=True).exists():
             # already unlocked
            return Response({'error': 'Already unlocked'}, status=400)
        
        # create or get unlock request
        unlock, created = PropertyUnlock.objects.get_or_create(
            property=property_obj,
            customer=request.user,
            defaults={
            "unlock_fee": property_obj.unlock_fee,
            "is_unlocked": False
            })

        return Response({
            "property_unlock_id": unlock.id,
            "amount": str(property_obj.unlock_fee),
            "message": "Now initiate payment using /payments/initiate_payment/"
            }, status=201)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def full_details(self, request, pk=None):
        """Get full property details if unlocked by user"""
        property_obj = self.get_object()
        
        # Check if user is owner or has unlocked
        if request.user == property_obj.owner:
            serializer = PropertySerializer(property_obj, context={'request': request})
            return Response(serializer.data)
        
        try:
            PropertyUnlock.objects.get(property=property_obj, customer=request.user)
            serializer = PropertySerializer(property_obj, context={'request': request})
            return Response(serializer.data)
        except PropertyUnlock.DoesNotExist:
            return Response({'error': 'Property locked. Unlock to view full details.'}, 
                          status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_properties(self, request):
        properties = Property.objects.filter(owner=request.user)
        serializer = PropertySerializer(properties, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def unlocked(self, request):
        """Get all properties successfully unlocked by user"""
        unlocks = PropertyUnlock.objects.filter(
            customer=request.user,
            is_unlocked=True
            ).select_related('property')

        properties = [unlock.property for unlock in unlocks]
        serializer = PropertySerializer(properties,many=True,context={'request': request})
        return Response(serializer.data)
