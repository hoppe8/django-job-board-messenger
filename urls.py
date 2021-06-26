from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path("", login_required(views.messenger, login_url="/accounts/login"), name="messages"),
    path("<str:room_id>/", login_required(views.room, login_url="/accounts/login"), name="room"),
]
