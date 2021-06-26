import json
import datetime

from asgiref.sync import async_to_sync

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.humanize.templatetags.humanize import naturalday

from channels.generic.websocket import WebsocketConsumer

from .models import ChatRoom, ChatMessage
from accounts.models import User
from jobs.models import Application


class ChatConsumer(WebsocketConsumer):
    def fetch_messages(self, data):
        messages = ChatMessage.get_last_10_messages(room_id=self.room_id)

        content = {
            "command": "messages",
            "messages": self.messages_to_json(messages)
        }

        self.send_message(content)

    
    def new_message(self, data):
        author_id = data["author_id"]

        room = get_object_or_404(ChatRoom, room_id=self.room_id)
        author_user = get_object_or_404(User, user_id=author_id)

        # Verify author belongs to room
        if author_user.is_employer and author_user.pk == room.user1.pk:
            pass
        elif author_user.is_applicant and author_user.pk == room.user2.pk:
            pass
        else:
            raise PermissionDenied

        message = ChatMessage.objects.create(
            room = room,
            author = author_user,
            content = data["message"]
        )

        room.last_message_timestamp = message.timestamp

        if author_user.is_employer:
            room.user2_num_unread_messages += 1
        elif author_user.is_applicant:
            room.user1_num_unread_messages += 1

        room.save()

        content = {
            "command": "new_message",
            "message": self.message_to_json(message)
        }

        return self.send_chat_message(content)


    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))

        return result


    def message_to_json(self, message):
        author_display = message.author.first_name + " " + message.author.last_name
        if message.author.is_applicant:
            job_id = message.room.job_listing.pk
            job_title = message.room.job_listing.job_title
            status = get_object_or_404(Application, user=message.room.user2, job_listing=message.room.job_listing).status
            company = False
        elif message.author.is_employer:
            company = message.author.employer.company
            job_id = False
            job_title = False
            status = False

        else:
            pass

        timestamp = humanize_timestamp(message.timestamp, False)
        panel_timestamp = humanize_timestamp(message.timestamp, True)

        return {
            "message_id": message.pk,
            "author": message.author.pk,
            "author_display": author_display,
            "content": message.content,
            "timestamp": timestamp,
            "panel_timestamp": panel_timestamp,
            "job_id": job_id,
            "job_title": job_title,
            "status": status,
            "company": company,
        }


    commands = {
        "fetch_messages": fetch_messages,
        "new_message": new_message,
    }


    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat_%s' % self.room_id

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data["command"]](self, data)


    def send_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps(message))

        room = get_object_or_404(ChatRoom, room_id=self.room_id)

        if not room.user1_is_active:
            room.user1_is_active = True
        elif not room.user2_is_active:
            room.user2_is_active = True

        room.save()


def humanize_timestamp(timestamp, for_panel):
    # new message that will only be displayed via js
    if for_panel:
        timestamp = str(int(timestamp.strftime("%I"))) + ":" + timestamp.strftime("%M") + " " + timestamp.strftime("%p")
    elif naturalday(timestamp) == "today":
        timestamp = "Today, " + str(int(timestamp.strftime("%I"))) + ":" + timestamp.strftime("%M") + " " + timestamp.strftime("%p")
    elif naturalday(timestamp) == "yesterday":
        timestamp = "Yesterday, " + str(int(timestamp.strftime("%I"))) + ":" + timestamp.strftime("%M") + " " + timestamp.strftime("%p")
    elif datetime.datetime.now().strftime("%Y") == timestamp.strftime("%Y"):
        timestamp = timestamp.strftime("%B") + " " + str(int(timestamp.strftime("%d"))) + ", " + str(int(timestamp.strftime("%I"))) + ":" + timestamp.strftime("%M") + " " + timestamp.strftime("%p")
    else:
        timestamp = timestamp.strftime("%B") + " " + str(int(timestamp.strftime("%d"))) + ", " + timestamp.strftime("%Y")

    return timestamp



