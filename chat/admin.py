from django.contrib import admin
from .models import ChatRoom, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'text', 'image', 'is_read', 'created_at')
    can_delete = True


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'product', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = (
        'buyer__username',
        'buyer__email',
        'seller__username',
        'seller__email',
        'product__name',
    )
    raw_id_fields = ('buyer', 'seller', 'product')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'short_text', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'sender__email', 'text')
    raw_id_fields = ('room', 'sender')

    def short_text(self, obj):
        return obj.text[:50] if obj.text else "[Image Message]"
    short_text.short_description = "Message"