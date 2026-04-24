"""
Push notification service for managing push subscriptions and sending notifications
"""

import json
import logging
from typing import Dict, List, Optional

try:
    from pywebpush import WebPushException, webpush
except ImportError:
    webpush = None
    WebPushException = Exception
from django.conf import settings
from django.utils import timezone

from .models import User
from .push_models import PushNotificationLog, PushSubscription

logger = logging.getLogger("nogoff")


class PushNotificationService:
    """Service for managing push notifications"""

    def __init__(self):
        """Initialize push notification service with VAPID keys"""
        self.vapid_public_key = getattr(settings, "PUSH_VAPID_PUBLIC_KEY", None)
        self.vapid_private_key = getattr(
            settings, "PUSH_VAPID_PRIVATE_KEY", None
        )
        self.vapid_email = getattr(
            settings, "PUSH_VAPID_EMAIL", "admin@example.com"
        )

        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("VAPID keys not configured for push notifications")

    def register_subscription(
        self, user: User, subscription_json: Dict, user_agent: str = ""
    ) -> PushSubscription:
        """
        Register or update a push subscription for a user

        Args:
            user: User object
            subscription_json: Subscription object from client (endpoint, keys, etc.)
            user_agent: Optional user agent string

        Returns:
            PushSubscription object
        """
        try:
            # Create or update subscription
            subscription, created = PushSubscription.objects.update_or_create(
                user=user,
                subscription_json=subscription_json,
                defaults={
                    "user_agent": user_agent,
                    "is_active": True,
                },
            )

            action = "registered" if created else "updated"
            logger.info(f"Push subscription {action} for user {user.name}")
            return subscription
        except Exception as e:
            logger.error(
                f"Error registering push subscription for user {user.name}: {str(e)}"
            )
            raise

    def unregister_subscription(
        self, user: User, subscription_json: Dict
    ) -> bool:
        """
        Unregister a push subscription

        Args:
            user: User object
            subscription_json: Subscription object to remove

        Returns:
            True if successfully removed, False otherwise
        """
        try:
            subscription = PushSubscription.objects.filter(
                user=user, subscription_json=subscription_json
            ).first()

            if subscription:
                subscription.delete()
                logger.info(f"Push subscription removed for user {user.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unregistering push subscription: {str(e)}")
            raise

    def send_notification(
        self,
        user: User,
        title: str,
        body: str,
        notification_type: str = "notification",
        options: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """
        Send a push notification to a user

        Args:
            user: User object
            title: Notification title
            body: Notification body/message
            notification_type: Type of notification (for logging)
            options: Additional options (icon, badge, tag, etc.)

        Returns:
            Dictionary with results for each subscription
        """
        if not self.vapid_private_key:
            logger.error(
                "Cannot send push notification: VAPID keys not configured"
            )
            return {"error": "VAPID keys not configured"}

        subscriptions = PushSubscription.objects.filter(
            user=user, is_active=True
        )

        if not subscriptions.exists():
            logger.info(f"No active push subscriptions for user {user.name}")
            return {"warning": "No subscriptions found"}

        payload = self._build_payload(title, body, options)
        results = {}

        for subscription in subscriptions:
            try:
                webpush(
                    subscription=subscription.subscription_json,
                    data=json.dumps(payload),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims={
                        "sub": self.vapid_email,
                    },
                )

                results[subscription.id] = {"status": "sent"}

                # Log successful notification
                PushNotificationLog.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    status="sent",
                    sent_at=timezone.now(),
                )

                logger.info(f"Push notification sent to {user.name}")

            except WebPushException as e:
                error_msg = str(e)
                results[subscription.id] = {
                    "status": "failed",
                    "error": error_msg,
                }

                # Log failed notification
                PushNotificationLog.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    status="failed",
                    error_message=error_msg,
                )

                # Disable subscription if endpoint is no longer valid
                if (
                    "410" in error_msg
                    or "invalid endpoint" in error_msg.lower()
                ):
                    subscription.is_active = False
                    subscription.save()
                    logger.warning(
                        f"Disabled invalid push subscription for {user.name}"
                    )
                else:
                    logger.error(
                        f"Failed to send push notification to {user.name}: {error_msg}"
                    )

            except Exception as e:
                error_msg = str(e)
                results[subscription.id] = {
                    "status": "failed",
                    "error": error_msg,
                }
                logger.exception(
                    f"Unexpected error sending push notification: {error_msg}"
                )

        return results

    def send_notification_to_all_users(
        self,
        title: str,
        body: str,
        notification_type: str = "broadcast",
        users: Optional[List[User]] = None,
        options: Optional[Dict] = None,
    ) -> Dict:
        """
        Send a notification to multiple users

        Args:
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            users: List of User objects (if None, sends to all users)
            options: Additional notification options

        Returns:
            Dictionary with results for each user
        """
        if users is None:
            users = User.objects.all()

        results = {}
        for user in users:
            results[user.id] = self.send_notification(
                user, title, body, notification_type, options
            )

        return results

    @staticmethod
    def _build_payload(
        title: str, body: str, options: Optional[Dict] = None
    ) -> Dict:
        """Build notification payload"""
        payload = {
            "notification": {
                "title": title,
                "body": body,
                "icon": "/static/images/icon.png",
                "badge": "/static/images/badge.png",
                "tag": "nogoff-notification",
            }
        }

        if options:
            payload["notification"].update(options)

        return payload


# Create a singleton instance
push_service = PushNotificationService()
