from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from .forms import GroupCreateForm
from .models import ChatRoom, RoomMembership


@login_required
def chat_home_view(request):
    users = User.objects.exclude(id=request.user.id).order_by("username")
    rooms = (
        ChatRoom.objects.filter(members__user=request.user)
        .distinct()
        .prefetch_related("members__user")
    )
    return render(request, "messenger/chat_home.html", {
        "users": users,
        "rooms": rooms,
    })


@login_required
def start_private_chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    existing_rooms = ChatRoom.objects.filter(
        room_type="private",
        members__user=request.user,
    ).distinct()

    room = None
    for r in existing_rooms:
        member_ids = set(r.members.values_list("user_id", flat=True))
        if member_ids == {request.user.id, other_user.id}:
            room = r
            break

    if room is None:
        room = ChatRoom.objects.create(
            room_type="private",
            created_by=request.user,
        )
        RoomMembership.objects.create(room=room, user=request.user)
        RoomMembership.objects.create(room=room, user=other_user)

    return redirect("chat_room", room_id=room.id)


@login_required
def create_group_view(request):
    form = GroupCreateForm(request.POST or None)
    form.fields["members"].queryset = User.objects.exclude(id=request.user.id).order_by("username")

    if request.method == "POST" and form.is_valid():
        room = form.save(commit=False)
        room.room_type = "group"
        room.created_by = request.user
        room.save()

        RoomMembership.objects.create(room=room, user=request.user)
        for user in form.cleaned_data["members"]:
            RoomMembership.objects.create(room=room, user=user)

        return redirect("chat_room", room_id=room.id)

    return render(request, "messenger/group_create.html", {"form": form})


@login_required
def chat_room_view(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, members__user=request.user)
    messages = room.messages.select_related("sender").all()
    members = room.members.select_related("user").all()
    rooms = (
        ChatRoom.objects.filter(members__user=request.user)
        .distinct()
        .prefetch_related("members__user")
    )
    users = User.objects.exclude(id=request.user.id).order_by("username")

    return render(request, "messenger/chat_room.html", {
        "room": room,
        "messages": messages,
        "members": members,
        "rooms": rooms,
        "users": users,
    })