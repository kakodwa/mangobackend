from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.services.delivery_analytics import get_delivery_dashboard_stats


class DeliveryDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_delivery_dashboard_stats(request.user)
        return Response(data)