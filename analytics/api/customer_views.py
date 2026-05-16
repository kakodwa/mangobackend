from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.permissions import IsCustomer
from analytics.services.customer_analytics import get_customer_dashboard_stats


class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        data = get_customer_dashboard_stats(request.user)
        return Response(data)