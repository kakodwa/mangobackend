# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from .models import AppEvent

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone
import datetime
import json


def analytics_dashboard_page(request):
    """
    Renders the HTML analytics dashboard interface template view 
    pre-loaded with aggregated AppEvent metrics and GPS tracking data coordinates.
    """
    # 1. Platform / Device Type Distribution
    device_metrics = list(AppEvent.objects.values('device_type')
                          .annotate(total=Count('id'))
                          .order_by('-total'))
    
    # 2. Top Engagement Features
    event_metrics = list(AppEvent.objects.values('event_name')
                         .annotate(total=Count('id'))
                         .order_by('-total')[:7])
    
    # 3. Timeline Sequence Trends (Last 7 Days)
    one_week_ago = timezone.now() - datetime.timedelta(days=7)
    timeline_metrics = list(AppEvent.objects.filter(timestamp__gte=one_week_ago)
                            .annotate(day=TruncDay('timestamp'))
                            .values('day')
                            .annotate(total=Count('id'))
                            .order_by('day'))
    
    for item in timeline_metrics:
        item['day'] = item['day'].strftime('%b %d')

    # 4. GPS Permission Splits
    gps_allowed = AppEvent.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
    gps_denied = AppEvent.objects.filter(latitude__isnull=True).count()

    # 5. NEW: GPS Coordinate Hot Spot Extraction
    # Pulls all events containing valid location telemetry fields
    gps_points = list(AppEvent.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).values_list('latitude', 'longitude'))

    # Consolidate all data pipelines
    chart_data = {
        'devices': device_metrics,
        'events': event_metrics,
        'timeline': timeline_metrics,
        'gps': {
            'allowed': gps_allowed,
            'denied': gps_denied
        },
        'locations': gps_points # Nested structure format: [[lat1, lng1], [lat2, lng2], ...]
    }

    context = {
        'chart_data_json': json.dumps(chart_data)
    }

    return render(request, 'analytics/analytics_dashboard.html', context)


class LogEventView(APIView):
    def post(self, request):
        event_name = request.data.get('event_name')
        device_type = request.data.get('device_type')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not event_name or not device_type:
            return Response({"error": "Missing data"}, status=status.HTTP_400_BAD_REQUEST)
            
        AppEvent.objects.create(
            event_name=event_name, 
            device_type=device_type,
            latitude=latitude,
            longitude=longitude
        )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


class GetStatsView(APIView):
    """Endpoint for Flutter to retrieve aggregated totals"""
    def get(self, request):
        # 1. Total events recorded
        total_events = AppEvent.objects.count()
        
        # 2. Break down by device type (e.g., {"iOS": 50, "Android": 120})
        device_breakdown = AppEvent.objects.values('device_type').annotate(count=Count('device_type'))
        device_stats = {item['device_type']: item['count'] for item in device_breakdown}
        
        # 3. Break down by individual button clicks
        click_breakdown = AppEvent.objects.values('event_name').annotate(count=Count('event_name'))
        click_stats = {item['event_name']: item['count'] for item in click_breakdown}

        return Response({
            "total_logs": total_events,
            "devices": device_stats,
            "clicks": click_stats
        }, status=status.HTTP_200_OK)
