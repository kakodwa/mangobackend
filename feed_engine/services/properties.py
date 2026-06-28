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
from hospitality.serializers import LodgeSerializer
from realestate.serializers import PropertySerializer


class PropertyFeedService(BaseFeedService):

    def get_feed(self, cursor=None, user=None, request=None):
        last_id = Cursor.decode(cursor)

        serializer_context = (
            {"request": request}
            if request
            else {}
        )

        # =====================================
        # PRIMARY CONTENT (PROPERTIES)
        # =====================================
        properties_qs = self.paginate(
            get_properties(),
            last_id,
        )

        properties = list(properties_qs)

        if not properties:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(
            properties[-1].id
        )

        serialized_properties = PropertySerializer(
            properties,
            many=True,
            context=serializer_context,
        ).data

        # FIXED: Populating from serialized_properties instead of an undefined 'feed' variable
        flat_properties_stream = [
            self.format_item("property", property_item)
            for property_item in serialized_properties
        ]

        # =====================================
        # SECONDARY CONTENT
        # =====================================
        trending_products = ProductSerializer(
            get_trending()[:10],
            many=True,
            context=serializer_context,
        ).data

        featured_shops = ShopSerializer(
            get_featured()[:10],
            many=True,
            context=serializer_context,
        ).data

        upcoming_events = EventSerializer(
            get_upcoming()[:10],
            many=True,
            context=serializer_context,
        ).data

        featured_lodges = LodgeSerializer(
            get_lodges()[:10],
            many=True,
            context=serializer_context,
        ).data

        # Exclude properties already displayed
        property_ids = [
            property_item.id
            for property_item in properties
        ]

        recommended_properties = PropertySerializer(
            get_properties().exclude(
                id__in=property_ids
            )[:10],
            many=True,
            context=serializer_context,
        ).data

        # =====================================
        # FEED INJECTION
        # =====================================
        mixed_stream = FeedInjector.inject(
            items_list=flat_properties_stream,
            injection_interval=12,
            products=trending_products,
            shops=featured_shops,
            events=upcoming_events,
            properties=recommended_properties,
            lodges=featured_lodges,
        )

        # =====================================
        # POST-PROCESS: Group back into grids of max 12
        # =====================================
        feed = []
        current_grid = []

        for item in mixed_stream:
            if item["type"] == "property":
                current_grid.append(item["data"])
                
                if len(current_grid) == 12:
                    feed.append(self.format_item("property_grid", current_grid))
                    current_grid = []
            else:
                if current_grid:
                    feed.append(self.format_item("property_grid", current_grid))
                    current_grid = []
                feed.append(item)

        if current_grid:
            feed.append(self.format_item("property_grid", current_grid))

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }