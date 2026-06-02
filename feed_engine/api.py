from rest_framework.views import APIView
from rest_framework.response import Response

from .services.properties import PropertyFeedService
from .services.home import HomeFeedService
from .services.shop import ShopFeedService
from .services.event import EventFeedService
from .services.lodge import LodgeFeedService


class HomeFeedAPI(APIView):
    def get(self, request):
        cursor = request.query_params.get("cursor")
        data = HomeFeedService().get_feed(cursor, request.user)
        return Response(data)


class ShopFeedAPI(APIView):
    def get(self, request):
        cursor = request.query_params.get("cursor")
        data = ShopFeedService().get_feed(cursor, request.user)
        return Response(data)


class EventFeedAPI(APIView):
    def get(self, request):
        cursor = request.query_params.get("cursor")
        data = EventFeedService().get_feed(cursor, request.user)
        return Response(data)


class LodgeFeedAPI(APIView):
    def get(self, request):
        cursor = request.query_params.get("cursor")
        data = LodgeFeedService().get_feed(cursor, request.user)
        return Response(data)




class PropertyFeedAPI(APIView):

    def get(self, request):
        cursor = request.query_params.get("cursor")

        data = PropertyFeedService().get_feed(
            cursor=cursor,
            user=request.user,
            request=request,
        )

        return Response(data)