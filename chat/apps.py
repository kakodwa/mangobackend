# chat/apps.py

from django.apps import AppConfig
from django.db.backends.signals import connection_created

def set_utf8mb4(sender, connection, **kwargs):
    if connection.vendor == 'mysql':
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute("SET CHARACTER SET utf8mb4;")

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        connection_created.connect(set_utf8mb4)