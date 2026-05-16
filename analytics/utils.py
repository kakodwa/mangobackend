from datetime import timedelta
from django.utils import timezone


def get_date_range(days=30):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date