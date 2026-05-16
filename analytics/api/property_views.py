from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.permissions import IsPropertyOwner
from analytics.services.property_analytics import get_property_dashboard_stats


class PropertyDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsPropertyOwner]

    def get(self, request):
        data = get_property_dashboard_stats(request.user)
        return Response(data)