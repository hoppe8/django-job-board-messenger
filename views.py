import json
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib.humanize.templatetags.humanize import naturalday

from .models import ChatRoom, ChatMessage
from jobs.models import JobListing, Application


@login_required
def messenger(request):
    if request.user.is_employer:
        try: q = int(request.GET.get("q"))
        except: q = False

        if q != False:
            t = get_object_or_404(JobListing, job_listing_id=q)
            rooms = ChatRoom.objects.filter(user1=request.user, job_listing=t).order_by("-last_message_timestamp").reverse()
        else:
            rooms = ChatRoom.objects.filter(user1=request.user).order_by("-last_message_timestamp").reverse()

        inactive_rooms = get_inactive_rooms(request, q=q)
        job_listings = JobListing.objects.filter(user=request.user)

    elif request.user.is_applicant:
        rooms = ChatRoom.objects.filter(user2=request.user).order_by("-last_message_timestamp").reverse()
        inactive_rooms = get_inactive_rooms(request, q=False)

        q = False
        job_listings = False

    else:
        raise Http404

    if len(rooms) < 1:
        rooms = False
        room_pks = False
    else:
        rooms = rooms.reverse()
        room_pks = [room.pk for room in rooms]

        statuses = []
        all_rooms_inactive = True
        for room in rooms:
            statuses.append(get_object_or_404(Application, user=room.user2, job_listing=room.job_listing).status)

            # if all rooms are inactive, rooms can be set to False
            if request.user.is_employer and room.user1_is_active:
                all_rooms_inactive = False
            elif request.user.is_applicant and room.user2_is_active:
                all_rooms_inactive = False
            else:
                pass

        if all_rooms_inactive:
            rooms = False
        else:
            rooms = zip(rooms, get_last_messages(rooms), statuses)

    if inactive_rooms != False:
        inactive_room_statuses = []
        for room in inactive_rooms:
            inactive_room_statuses.append(get_object_or_404(Application, user=room.user2, job_listing=room.job_listing).status)

        inactive_rooms = zip(inactive_rooms, inactive_room_statuses)


    context = {
        "rooms": rooms,
        "room_pks": room_pks,
        "inactive_rooms": inactive_rooms,
        "job_id": q,
        "job_listings": job_listings,
    }

    return render(request, "messenger/index.html", context)


@login_required
def room(request, room_id):
    try: q = int(request.GET.get("q"))
    except: q = False

    if request.method == "POST":
        if "action" in request.POST:
            if request.POST["action"] == "close":
                if request.user.is_employer:
                    room = get_object_or_404(ChatRoom, room_id=room_id, user1=request.user)
                    room.user1_is_active = False
                elif request.user.is_applicant:
                    room = get_object_or_404(ChatRoom, room_id=room_id, user2=request.user)
                    room.user2_is_active = False
                else:
                    raise Http404

                room.save()

                return HttpResponse(json.dumps({}), content_type="application/json")
        else:
            raise Http404

    elif request.method == "GET":
        if "action" in request.GET:
            if request.GET["action"] == "read":
                if request.user.is_employer:
                    room = get_object_or_404(ChatRoom, room_id=room_id, user1=request.user)
                    room.user1_num_unread_messages = 0
                elif request.user.is_applicant:
                    room = get_object_or_404(ChatRoom, room_id=room_id, user2=request.user)
                    room.user2_num_unread_messages = 0
                else:
                    raise Http404

                room.save()
                return HttpResponse(json.dumps({}), content_type="application/json")

        if request.user.is_employer:
            try: q = int(request.GET.get("q"))
            except: q = False

            if q != False:
                t = get_object_or_404(JobListing, job_listing_id=q)
                rooms = ChatRoom.objects.filter(user1=request.user, job_listing=t).order_by("-last_message_timestamp").reverse()
            else:
                rooms = ChatRoom.objects.filter(user1=request.user).order_by("-last_message_timestamp").reverse()

            room = get_object_or_404(ChatRoom, room_id=room_id, user1=request.user)
            app_status = get_object_or_404(Application, user=room.user2, job_listing=room.job_listing).status

            job_listings = JobListing.objects.filter(user=request.user)

            recipient = room.user2

        elif request.user.is_applicant:
            rooms = ChatRoom.objects.filter(user2=request.user).order_by("-last_message_timestamp").reverse()
            room = get_object_or_404(ChatRoom, room_id=room_id, user2=request.user)
            app_status = False

            q = False
            job_listings = False

            recipient = room.user1

        else:
            raise Http404


        if request.user.is_employer:
            if not room.user1_is_active:
                room.user1_is_active = True

            room.user1_num_unread_messages = 0
            room.save()

            inactive_rooms = get_inactive_rooms(request, q)

        elif request.user.is_applicant:
            if not room.user2_is_active:
                room.user2_is_active = True

            room.user2_num_unread_messages = 0
            room.save()

            inactive_rooms = get_inactive_rooms(request, q=False)

        else:
            raise Http404

        rooms = rooms.reverse()
        room_pks = [room.pk for room in rooms]

        statuses = []
        for app_room in rooms:
            statuses.append(get_object_or_404(Application, user=app_room.user2, job_listing=app_room.job_listing).status)

        rooms = zip(rooms, get_last_messages(rooms), statuses)
    
        if inactive_rooms != False:
            inactive_room_statuses = []
            for app_room in inactive_rooms:
                inactive_room_statuses.append(get_object_or_404(Application, user=app_room.user2, job_listing=app_room.job_listing).status)

            inactive_rooms = zip(inactive_rooms, inactive_room_statuses)


        context = {
            "current_room": room,
            "app_status": app_status,
            "rooms": rooms,
            "room_pks": room_pks,
            "inactive_rooms": inactive_rooms,
            "job_listings": job_listings,
            "job_id": q,
            "messages": False,
            "author_id": request.user.pk,
            "recipient_id": recipient.pk,
        }

        return render(request, "messenger/room.html", context)

    else:
        raise Http404


def get_inactive_rooms(request, q):
    if request.user.is_employer:
        if q != False:
            job_listing = get_object_or_404(JobListing, job_listing_id=q)
            rooms1 = ChatRoom.objects.filter(user1=request.user, job_listing=job_listing)
        else:
            rooms1 = ChatRoom.objects.filter(user1=request.user)

        inactive_rooms = []
        for i, room1 in enumerate(rooms1):
            if room1.user1_is_active == False:
                inactive_rooms.append(room1)

    elif request.user.is_applicant:
        rooms1 = ChatRoom.objects.filter(user2=request.user)
        inactive_rooms = []
        for i, room1 in enumerate(rooms1):
            if room1.user2_is_active == False:
                inactive_rooms.append(room1)

    if len(inactive_rooms) < 1:
        inactive_rooms = False

    return inactive_rooms


def get_last_messages(rooms):
    last_messages_obj = []
    for room in rooms:
        last_messages_obj.append(ChatMessage.get_last_message_for_dialog(room))

    last_messages = []
    for message in last_messages_obj:
        if message == None:
            last_messages.append(["This is the beginning of your direct message history with...", ""])
            continue

        if naturalday(message.timestamp) == "today":
            last_messages.append([message.content, str(int(message.timestamp.strftime("%I"))) + ":" + message.timestamp.strftime("%M") + " " + message.timestamp.strftime("%p")])
        elif naturalday(message.timestamp) == "yesterday":
            last_messages.append([message.content, "Yesterday"])
        elif datetime.datetime.now().strftime("%Y") == message.timestamp.strftime("%Y"):
            last_messages.append([message.content, message.timestamp.strftime("%b") + " " + str(int(message.timestamp.strftime("%d")))])
        else:
            last_messages.append([message.content, message.timestamp.strftime("%b") + " " + str(int(message.timestamp.strftime("%d"))) + ", " + message.timestamp.strftime("%Y")])

    return last_messages


