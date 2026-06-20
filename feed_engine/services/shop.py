from ..services.base import BaseFeedService
from ..services.cursor import Cursor
from ..services.injector import FeedInjector

from ..selectors.shops import get_shops, get_featured
from ..selectors.products import get_trending
from ..selectors.events import get_upcoming
from ..selectors.properties import get_properties
from ..selectors.lodges import get_lodges

from realestate.serializers import PropertySerializer
from hospitality.serializers import LodgeSerializer
from shops.serializers import ShopSerializer
from products.serializers import ProductSerializer
from events.serializers import EventSerializer


class ShopFeedService(BaseFeedService):

    def get_feed(self, cursor=None, user=None, request=None):
        last_id = Cursor.decode(cursor)

        serializer_context = (
            {"request": request}
            if request
            else {}
        )

        # =====================================
        # PRIMARY CONTENT (SHOPS)
        # =====================================

        shops_qs = self.paginate(
            get_shops(),
            last_id,
        )

        shops = list(shops_qs)

        if not shops:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(
            shops[-1].id
        )

        serialized_shops = ShopSerializer(
            shops,
            many=True,
            context=serializer_context,
        ).data

        feed = [
            self.format_item(
                "shop",
                serialized_shops,
                #shop,
            )
            for shop in serialized_shops
        ]

        # =====================================
        # SECONDARY CONTENT
        # =====================================

        trending_products = ProductSerializer(
            get_trending()[:10],
            many=True,
            context=serializer_context,
        ).data

        upcoming_events = EventSerializer(
            get_upcoming()[:10],
            many=True,
            context=serializer_context,
        ).data

        featured_properties = PropertySerializer(
            get_properties()[:10],
            many=True,
            context=serializer_context,
        ).data

        featured_lodges = LodgeSerializer(
            get_lodges()[:10],
            many=True,
            context=serializer_context,
        ).data

        # Avoid duplicating shops already
        # displayed in the main feed

        shop_ids = [
            shop.id
            for shop in shops
        ]

        featured_shops = ShopSerializer(
            get_featured().exclude(
                id__in=shop_ids
            )[:10],
            many=True,
            context=serializer_context,
        ).data

        # =====================================
        # FEED INJECTION
        # =====================================

        feed = FeedInjector.inject(
            feed=feed,
            products=trending_products,
            shops=featured_shops,
            events=upcoming_events,
            properties=featured_properties,
            lodges=featured_lodges,
        )

        # =====================================
        # RESPONSE
        # =====================================

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }