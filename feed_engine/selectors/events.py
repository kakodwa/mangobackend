from events.models import Event


def get_events():
    return Event.objects.all()


def get_upcoming():
    return Event.objects.order_by("event_date")[:20]