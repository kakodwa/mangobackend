# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from .models import AppEvent

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rembg import remove
import io



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



@csrf_exempt  # Exempting for testing; use proper auth/tokens in production!
def remove_product_background(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # 1. Read the uploaded image from Flutter into memory
            uploaded_file = request.FILES['image']
            input_data = uploaded_file.read()
            
            # 2. Process image through the AI engine
            # rembg outputs raw bytes of a transparent PNG
            output_data = remove(input_data)
            
            # 3. Return the processed transparent image directly to Flutter
            return HttpResponse(output_data, content_type="image/png")
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request. Please POST an image.'}, status=400)