from ..services.base import BaseFeedService
from ..services.cursor import Cursor
from ..services.injector import FeedInjector

from ..selectors.events import get_events
from ..selectors.products import get_trending
from ..selectors.shops import get_featured
from ..selectors.properties import get_properties
from ..selectors.lodges import get_lodges

from shops.serializers import ShopSerializer
from realestate.serializers import PropertySerializer
from hospitality.serializers import LodgeSerializer
from events.serializers import EventSerializer
from products.serializers import ProductSerializer


class EventFeedService(BaseFeedService):

    def get_feed(self, cursor=None, user=None, request=None):
        last_id = Cursor.decode(cursor)

        serializer_context = (
            {"request": request}
            if request
            else {}
        )

        # =====================================
        # PRIMARY EVENTS
        # =====================================
        events_qs = self.paginate(
            get_events(),
            last_id,
        )

        events = list(events_qs)

        if not events:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(
            events[-1].id
        )

        serialized_events = EventSerializer(
            events,
            many=True,
            context=serializer_context,
        ).data

        # FIXED: Populating from serialized_events instead of an undefined 'feed' variable
        flat_events_stream = [
            self.format_item("event", event)
            for event in serialized_events
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

        # =====================================
        # RECOMMENDED EVENTS
        # =====================================
        event_ids = [
            event.id
            for event in events
        ]

        recommended_events = EventSerializer(
            get_events().exclude(
                id__in=event_ids
            )[:10],
            many=True,
            context=serializer_context,
        ).data

        # =====================================
        # FEED INJECTION
        # =====================================
        mixed_stream = FeedInjector.inject(
            items_list=flat_events_stream,
            injection_interval=12,
            products=trending_products,
            shops=featured_shops,
            events=recommended_events,
            properties=featured_properties,
            lodges=featured_lodges,
        )

        # =====================================
        # POST-PROCESS: Group back into grids of max 12
        # =====================================
        feed = []
        current_grid = []

        for item in mixed_stream:
            if item["type"] == "event":
                current_grid.append(item["data"])
                
                if len(current_grid) == 12:
                    feed.append(self.format_item("event_grid", current_grid))
                    current_grid = []
            else:
                if current_grid:
                    feed.append(self.format_item("event_grid", current_grid))
                    current_grid = []
                feed.append(item)

        if current_grid:
            feed.append(self.format_item("event_grid", current_grid))

        return {
            "next_cursor": next_cursor,
            "results": feed,
        }