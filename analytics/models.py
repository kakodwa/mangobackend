# analytics/models.py
from django.db import models

class AppEvent(models.Model):
    event_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)
    
    # New GPS fields (blank=True, null=True allows anonymous users to deny permission)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_name} - {self.device_type} (GPS: {self.latitude}, {self.longitude})"