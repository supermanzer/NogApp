from django.urls import path

from . import push_views, views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("event/<int:nog_id>", views.event, name="event"),
    path("event/<int:nog_id>/vote/", views.vote, name="vote"),
    path("event/<int:nog_id>/reset-votes", views.reset_votes, name="reset"),
    # Push notification endpoints
    path(
        "api/push/subscribe/",
        push_views.subscribe_to_push,
        name="push_subscribe",
    ),
    path(
        "api/push/unsubscribe/",
        push_views.unsubscribe_from_push,
        name="push_unsubscribe",
    ),
    path(
        "api/push/public-key/",
        push_views.get_push_public_key,
        name="push_public_key",
    ),
]
