"""
Management command to check events for an approaching voting deadline
and send a push notification reminder once per event.
Usage: python manage.py check_voting_reminders
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from nogoff.models import Event, Settings
from nogoff.push_service import push_service


class Command(BaseCommand):
    help = "Send a push notification reminder for events whose voting is about to close"

    def handle(self, *args, **options):
        settings_obj = Settings.objects.first()
        if not settings_obj:
            self.stdout.write(
                self.style.WARNING(
                    "No Settings configured; skipping voting reminder check"
                )
            )
            return

        minutes_before = settings_obj.voting_reminder_minutes_before_end
        threshold = timedelta(minutes=minutes_before)
        now = timezone.now()

        candidates = Event.objects.filter(voting_reminder_sent_at__isnull=True)

        for event in candidates:
            end_datetime = event.end_datetime

            if end_datetime <= now:
                # Voting has already closed; too late for a "closing soon" reminder.
                continue

            if end_datetime - now > threshold:
                # Not yet within the reminder window.
                continue

            push_service.send_voting_reminder(
                event=event, minutes_remaining=minutes_before
            )
            event.voting_reminder_sent_at = now
            event.save(update_fields=["voting_reminder_sent_at"])

            self.stdout.write(
                self.style.SUCCESS(f"Sent voting reminder for '{event.name}'")
            )
