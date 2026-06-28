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
            last_id,
        )

        lodges = list(lodges_qs)

        if not lodges:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(
            lodges[-1].id
        )

        serialized_lodges = LodgeSerializer(
            lodges,
            many=True,
            context=serializer_context,
        ).data

        # FIXED: Populating from serialized_lodges instead of an undefined 'feed' variable
        flat_lodges_stream = [
            self.format_item("lodge", lodge)
            for lodge in serialized_lodges
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

        featured_properties = PropertySerializer(
            get_properties()[:10],
            many=True,
            context=serializer_context,
        ).data

        # Exclude lodges already shown in feed
        lodge_ids = [lodge.id for lodge in lodges]

        recommended_lodges = LodgeSerializer(
            get_lodges().exclude(
                id__in=lodge_ids
            )[:10],
            many=True,
            context=serializer_context,
        ).data

        # =====================================
        # FEED INJECTION
        # =====================================
        mixed_stream = FeedInjector.inject(
            items_list=flat_lodges_stream,
            injection_interval=12,
            products=trending_products,
            shops=featured_shops,
            events=upcoming_events,
            properties=featured_properties,
            lodges=recommended_lodges,
        )

        # =====================================
        # POST-PROCESS: Group back into grids of max 12
        # =====================================
        feed = []
        current_grid = []

        for item in mixed_stream:
            if item["type"] == "lodge":
                current_grid.append(item["data"])
                
                if len(current_grid) == 12:
                    feed.append(self.format_item("lodge_grid", current_grid))
                    current_grid = []
            else:
                if current_grid:
                    feed.append(self.format_item("lodge_grid", current_grid))
                    current_grid = []
                feed.append(item)

        if current_grid:
            feed.append(self.format_item("lodge_grid", current_grid))

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }