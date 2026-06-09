# mangohub/apps.py
from django.apps import AppConfig

class MangohubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mangohub'

    def ready(self):
        # 🔔 This forces Django to load and listen to your signals.py file!
        import mangohub.signals