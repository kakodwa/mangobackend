from ..services.base import BaseFeedService
from ..services.cursor import Cursor
from ..services.injector import FeedInjector

from ..selectors.products import get_trending
from ..selectors.shops import get_featured
from ..selectors.events import get_upcoming
from ..selectors.lodges import get_lodges
from ..selectors.properties import get_properties

from products.serializers import ProductSerializer
from shops.serializers import ShopSerializer
from events.serializers import EventSerializer
from realestate.serializers import PropertySerializer
from hospitality.serializers import LodgeSerializer


class LodgeFeedService(BaseFeedService):

    def get_feed(self, cursor=None, user=None, request=None):
        last_id = Cursor.decode(cursor)

        serializer_context = (
            {"request": request}
            if request
            else {}
        )

        # =====================================
        # PRIMARY CONTENT (LODGES)
        # =====================================

        lodges_qs = self.paginate(
            get_lodges(),
            last_id
        )

        lodges = list(lodges_qs)

        if not lodges:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(lodges[-1].id)

        serialized_lodges = LodgeSerializer(
            lodges,
            many=True,
            context=serializer_context
        ).data

        feed = [
            self.format_item("lodge", lodge)
            for lodge in serialized_lodges
        ]

        # =====================================
        # HORIZONTAL PRODUCTS
        # =====================================

        trending_products = ProductSerializer(
            get_trending()[:10],
            many=True,
            context=serializer_context
            ).data

        featured_shops = ShopSerializer(
            get_featured()[:10],
             many=True,
             context=serializer_context
             ).data
        upcoming_events = EventSerializer(
            get_upcoming()[:10],
            many=True,
            context=serializer_context
            ).data

        featured_properties = PropertySerializer(
            get_properties()[:10],
            many=True,
            context=serializer_context
            ).data

        # =====================================
        # FEED INJECTION
        # =====================================

        feed = FeedInjector.inject(
            feed=feed,
            products=trending_products,
            events=None,
            shops=None
        )

        # =====================================
        # RESPONSE
        # =====================================

        return {
            "next_cursor": next_cursor,
            "results": feed
        }