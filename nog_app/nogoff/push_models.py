"""
Push notification models for storing user push subscriptions
"""

from django.db import models

from .models import User


class PushSubscription(models.Model):
    """Store push notification subscriptions for users"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    subscription_json = models.JSONField(
        help_text="The subscription object from the Push API"
    )
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Push subscription for {self.user.name}"

    class Meta:
        unique_together = ("user", "subscription_json")


class PushNotificationLog(models.Model):
    """Log of push notifications sent"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="push_logs"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=50
    )  # e.g., 'event_reminder', 'voting_started', etc.
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type} to {self.user.name}"

    class Meta:
        ordering = ["-created_at"]
