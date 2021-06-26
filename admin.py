from django.contrib import admin

from .models import ChatRoom, ChatMessage


class ChatMessageAdmin(admin.ModelAdmin):
    readonly_fields = ("timestamp",)

admin.site.register(ChatRoom)
admin.site.register(ChatMessage, ChatMessageAdmin)
