from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from .services.admin_stats import get_admin_stats
from .services.user_stats import get_user_stats
from .services.shop_stats import get_shop_stats
from .services.property_stats import get_property_stats
from .services.delivery_stats import get_delivery_stats


class AnalyticsViewSet(ViewSet):

    def admin(self, request):
        return Response(get_admin_stats())

    def user(self, request):
        return Response(get_user_stats(request.user))

    def shop(self, request):
        return Response(get_shop_stats(request.user))

    def property(self, request):
        return Response(get_property_stats(request.user))

    def delivery(self, request):
        return Response(get_delivery_stats())



