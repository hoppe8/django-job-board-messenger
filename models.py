import datetime

from django.db import models

from accounts.models import User
from jobs.models import JobListing


class ChatRoom(models.Model):
    room_id = models.BigAutoField(primary_key=True)

    # Employer
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    # Applicant
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")

    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE)

    user1_is_active = models.BooleanField(default=False)
    user2_is_active = models.BooleanField(default=False)

    user1_num_unread_messages = models.PositiveSmallIntegerField(default=0)
    user2_num_unread_messages = models.PositiveSmallIntegerField(default=0)

    # For ordering purposes
    last_message_timestamp = models.DateTimeField(default=datetime.datetime(1900, 1, 1))


class ChatMessage(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pk)

    def get_last_10_messages(room_id):
        """ Need to asynchronously load messages, starting with 10.
            currently just loads last 100 messages (normal conversations
            should very rarely reach this number.
        """
        return ChatMessage.objects.filter(room_id=room_id).order_by('-timestamp').reverse()[:100]

    @staticmethod
    def get_last_message_for_dialog(room):
        return ChatMessage.objects.filter(room=room).last()


