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
            last_id
        )

        events = list(events_qs)

        if not events:
            return {
                "next_cursor": None,
                "results": []
            }

        next_cursor = Cursor.encode(events[-1].id)

        serialized_events = EventSerializer(
            events,
            many=True,
            context=serializer_context
        ).data

        feed = [
            self.format_item("event", event)
            for event in serialized_events
        ]

        # =====================================
        # HORIZONTAL PRODUCTS
        # =====================================
        # =====================================
        trending_products = ProductSerializer(
            get_trending()[:10],
            many=True,
            context=serializer_context).data

        featured_shops = ShopSerializer(
            get_featured()[:10],
            many=True,
            context=serializer_context
            ).data

        featured_properties = PropertySerializer(
            get_properties()[:10],
            many=True,
            context=serializer_context).data

        featured_lodges = LodgeSerializer(
            get_lodges()[:10],
            many=True,
            context=serializer_context
            ).data

        # =====================================
        # OPTIONAL EVENT BLOCKS
        # =====================================

        event_blocks = EventSerializer(
            get_events()[:10],
            many=True,
            context=serializer_context
        ).data

        # =====================================
        # INJECT CONTENT
        # =====================================

        feed = FeedInjector.inject(
            feed=feed,
            products=trending_products,
            events=event_blocks,
            shops=None
        )

        # =====================================
        # RESPONSE
        # =====================================

        return {
            "next_cursor": next_cursor,
            "results": feed
        }