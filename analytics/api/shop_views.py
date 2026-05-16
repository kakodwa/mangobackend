from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from analytics.permissions import IsShopOwner
from analytics.services.shop_analytics import get_shop_dashboard_stats


class ShopDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsShopOwner]

    def get(self, request):
        data = get_shop_dashboard_stats(request.user)
        return Response(data)