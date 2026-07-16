from django.apps import AppConfig

class AuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_app'

    def ready(self):
        import admin_app.signals  # 🌟 Force Django to load signal listeners on startup
