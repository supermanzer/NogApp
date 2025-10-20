from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("event/<int:nog_id>", views.event, name="event"),
    path("event/<int:nog_id>/vote/", views.vote, name="vote")
]
