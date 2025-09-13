from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def format_event_datetime(event):
    """Formats the event date and time."""
    if not event:
        return "No upcoming event"

    now = timezone.localtime(timezone.now())
    event_time = timezone.localtime(event.event_date)

    if event_time.date() == now.date():
        return f"Today, {event_time.strftime('%I:%M %p')}"
    elif (event_time.date() - now.date()).days == 1:
        return f"Tomorrow, {event_time.strftime('%I:%M %p')}"
    else:
        return event_time.strftime("%B %d, %Y, %I:%M %p")