from django.urls import path
from .views import chat_home_view, start_private_chat_view, create_group_view, chat_room_view

urlpatterns = [
    path("", chat_home_view, name="chat_home"),
    path("private/<int:user_id>/", start_private_chat_view, name="start_private_chat"),
    path("group/create/", create_group_view, name="create_group"),
    path("room/<int:room_id>/", chat_room_view, name="chat_room"),
]