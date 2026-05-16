from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.permissions import IsAdminUserType
from analytics.services.admin_analytics import get_admin_dashboard_stats


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def get(self, request):
        data = get_admin_dashboard_stats()
        return Response(data)