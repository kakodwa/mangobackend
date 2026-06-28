from ..services.base import BaseFeedService
from ..services.cursor import Cursor
from ..services.injector import FeedInjector

from ..selectors.products import get_products, get_trending
from ..selectors.shops import get_featured
from ..selectors.events import get_upcoming
from ..selectors.properties import get_properties
from ..selectors.lodges import get_lodges

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

        # Correctly map individual products from serialized_products
        flat_products_stream = [
            self.format_item("product", item)
            for item in serialized_products
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
        mixed_stream = FeedInjector.inject(
            items_list=flat_products_stream,
            injection_interval=12,
            products=trending_products,
            shops=featured_shops,
            events=upcoming_events,
            properties=featured_properties,
            lodges=featured_lodges,
        )

        # -----------------------------
        # POST-PROCESS: Group into Max 12 Grids
        # -----------------------------
        feed = []
        current_grid = []

        for item in mixed_stream:
            if item["type"] == "product":
                current_grid.append(item["data"])
                
                if len(current_grid) == 12:
                    feed.append(self.format_item("product_grid", current_grid))
                    current_grid = []
            else:
                if current_grid:
                    feed.append(self.format_item("product_grid", current_grid))
                    current_grid = []
                feed.append(item)

        if current_grid:
            feed.append(self.format_item("product_grid", current_grid))

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }