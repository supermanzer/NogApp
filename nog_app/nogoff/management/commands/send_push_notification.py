"""
Management command to send push notifications to users
Usage: python manage.py send_push_notification --title "Title" --body "Message" --type "notification_type"
"""

from django.core.management.base import BaseCommand

from nogoff.models import User
from nogoff.push_service import push_service


class Command(BaseCommand):
    help = "Send push notifications to users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--title", type=str, required=True, help="Notification title"
        )
        parser.add_argument(
            "--body", type=str, required=True, help="Notification body/message"
        )
        parser.add_argument(
            "--type",
            type=str,
            default="notification",
            help="Notification type (for logging)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Send to specific user ID (if not provided, sends to all users)",
        )

    def handle(self, *args, **options):
        title = options["title"]
        body = options["body"]
        notification_type = options["type"]
        user_id = options.get("user_id")

        try:
            if user_id:
                user = User.objects.get(pk=user_id)
                self.stdout.write(
                    f"Sending notification to user {user.name}..."
                )
                results = push_service.send_notification(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                )
            else:
                users = User.objects.all()
                self.stdout.write(
                    f"Sending notification to {users.count()} users..."
                )
                results = push_service.send_notification_to_all_users(
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    users=users,
                )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent "{title}" notification')
            )
            self.stdout.write(f"Results: {results}")

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error sending notification: {str(e)}")
            )
