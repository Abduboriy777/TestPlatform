from django.contrib import admin
from .models import ChatRoom, RoomMembership, ChatMessage

admin.site.register(ChatRoom)
admin.site.register(RoomMembership)
admin.site.register(ChatMessage)