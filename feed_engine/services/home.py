from ..services.base import BaseFeedService
from ..services.cursor import Cursor
from ..services.injector import FeedInjector

from ..selectors.products import get_products, get_trending
from ..selectors.shops import get_featured
from ..selectors.events import get_upcoming
from ..selectors.properties import get_properties
from ..selectors.lodges import  get_lodges

from products.serializers import ProductSerializer
from shops.serializers import ShopSerializer
from events.serializers import EventSerializer
from realestate.serializers import PropertySerializer
from hospitality.serializers import LodgeSerializer


class HomeFeedService(BaseFeedService):

    def get_feed(self, cursor, user, request=None):
        last_id = Cursor.decode(cursor)

        # -----------------------------
        # PRIMARY CONTENT
        # -----------------------------
        products_qs = self.paginate(
            get_products(),
            last_id,
        )

        products = list(products_qs)

        if not products:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(products[-1].id)

        serialized_products = ProductSerializer(
            products,
            many=True,
            context={"request": request} if request else {}
        ).data

        def chunk_list(data, size):
            return [
                data[i:i + size]
                for i in range(0, len(data), size)
            ]

        product_groups = chunk_list(
            serialized_products,
            2,
        )

        feed = [
            self.format_item(
                "product_grid",
                group,
            )
            for group in product_groups
        ]

        # -----------------------------
        # SECONDARY CONTENT
        # -----------------------------

        trending_products = ProductSerializer(
            get_trending(),
            many=True,
            context={"request": request} if request else {}
        ).data

        featured_shops = ShopSerializer(
            get_featured(),
            many=True,
            context={"request": request} if request else {}
        ).data

        upcoming_events = EventSerializer(
            get_upcoming(),
            many=True,
            context={"request": request} if request else {}
        ).data

        featured_properties = PropertySerializer(
            get_properties(),
            many=True,
            context={"request": request} if request else {}
        ).data

        featured_lodges = LodgeSerializer(
            get_lodges(),
            many=True,
            context={"request": request} if request else {}
        ).data

        # -----------------------------
        # INJECT CONTENT
        # -----------------------------

        feed = FeedInjector.inject(
            feed,
            products=trending_products,
            shops=featured_shops,
            events=upcoming_events,
            properties=featured_properties,
            lodges=featured_lodges,
        )

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }