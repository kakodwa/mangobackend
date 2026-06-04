# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from .models import AppEvent


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