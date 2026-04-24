# Push Notifications - Code Examples

This file contains practical examples for using push notifications in your NogApp.

## Example 1: Notify Users When Voting Starts

### In Django View

```python
# nog_app/nogoff/views.py

def start_voting_event(request: HttpRequest, event_id: int) -> HttpResponse:
    """View to start voting for an event"""
    try:
        event = Event.objects.get(pk=event_id)
        
        # Your voting start logic here
        event.is_open = True
        event.save()
        
        # Send push notification to all users
        from .push_service import push_service
        from .models import User
        
        all_users = User.objects.all()
        push_service.send_notification_to_all_users(
            title="🎄 Voting is Now Open!",
            body=f"Vote for your favorite nog in {event.name}",
            notification_type="voting_started",
            users=all_users,
            options={
                "icon": "/static/images/voting-icon.png",
                "tag": f"voting-{event.id}",
            }
        )
        
        return JsonResponse({"status": "success"})
    except Event.DoesNotExist:
        return JsonResponse({"error": "Event not found"}, status=404)
```

## Example 2: Scheduled Event Reminders (with Celery)

### Setup (Optional - requires Celery)

```python
# nog_app/nogoff/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Event, User
from .push_service import push_service

@shared_task
def send_event_reminders():
    """Send reminders for events starting in 1 hour"""
    now = timezone.now()
    one_hour_later = now + timedelta(hours=1)
    
    # Find events starting soon
    upcoming_events = Event.objects.filter(
        event_date__gte=now,
        event_date__lte=one_hour_later
    )
    
    for event in upcoming_events:
        # Only send if not already sent
        if not hasattr(event, 'reminder_sent') or not event.reminder_sent:
            all_users = User.objects.all()
            
            push_service.send_notification_to_all_users(
                title="Event Reminder",
                body=f"{event.name} is starting in 1 hour!",
                notification_type="event_reminder",
                users=all_users
            )
            
            # Mark as sent (you'd need to add this field to Event model)
            # event.reminder_sent = True
            # event.save()

# In celerybeat configuration, schedule this task:
# CELERY_BEAT_SCHEDULE = {
#     'send_event_reminders': {
#         'task': 'nogoff.tasks.send_event_reminders',
#         'schedule': crontab(minute=0),  # Every hour
#     },
# }
```

## Example 3: Custom Notification on Vote Confirmation

### In Vote View

```python
# nog_app/nogoff/views.py - Modified vote function

def vote(request: HttpRequest, nog_id: int) -> HttpResponse:
    if request.method == "POST":
        try:
            from .push_service import push_service
            
            user = getattr(request, "device_user", None)
            nogoff = Event.objects.get(pk=nog_id)
            data = dict(request.POST)
            _ = data.pop("csrfmiddlewaretoken")

            logger.info(f"Processing votes for event {nogoff}")
            user_logger.info(f"User {user} voting in event {nogoff}")

            vote_count = 0
            for id in data.keys():
                nog = Nog.objects.get(pk=int(id))
                votes = int(data[id][0])
                logger.debug(f"Processing {votes} votes for nog {nog}")
                for i in range(votes):
                    Vote(user=user, nog=nog, event=nogoff).save()
                    logger.debug(f"User {user} voted for Nog {nog}")
                    vote_count += votes

            user.has_voted = True
            user.save()
            user_logger.info(f"User {user} completed voting in event {nogoff}")

            # Send confirmation notification
            push_service.send_notification(
                user=user,
                title="✅ Votes Confirmed",
                body=f"Your {vote_count} votes have been recorded!",
                notification_type="vote_confirmation",
                options={
                    "tag": f"vote-confirmation-{nogoff.id}",
                }
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your votes have been recorded successfully!",
                }
            )
        except Event.DoesNotExist:
            logger.error(f"Event {nog_id} not found during voting")
            return JsonResponse(
                {"status": "error", "message": "Event not found"}, status=404
            )
        except Exception as e:
            logger.exception("Error processing votes")
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )
    else:
        logger.warning(f"Invalid method {request.method} for voting")
        return HttpResponseForbidden(content="GET method not permitted")
```

## Example 4: Frontend Button to Subscribe/Unsubscribe

### HTML with JavaScript

```html
<!-- nogoff/templates/nogoff/index.html -->

{% block body %}
<div id="notification-control">
    <button id="notif-btn" onclick="toggleNotifications()">
        📬 Enable Notifications
    </button>
    <span id="notif-status"></span>
</div>

<h1>Welcome to Nog Off</h1>
<hr />
{% include "nogoff/components/next_nogoff.html" %}
{% endblock %}

{% block script %}
<script>
    async function toggleNotifications() {
        const button = document.getElementById('notif-btn');
        const status = document.getElementById('notif-status');
        
        try {
            // Check if already subscribed
            const isSubscribed = await pushNotifications.isSubscribed();
            
            if (isSubscribed) {
                // Unsubscribe
                await pushNotifications.unsubscribe();
                button.textContent = '📬 Enable Notifications';
                status.textContent = 'Notifications disabled';
                status.style.color = 'gray';
            } else {
                // Request permission and subscribe
                const hasPermission = await pushNotifications.requestPermission();
                if (!hasPermission) {
                    status.textContent = 'Permission denied';
                    status.style.color = 'red';
                    return;
                }
                
                const success = await pushNotifications.subscribe();
                if (success) {
                    button.textContent = '📭 Disable Notifications';
                    status.textContent = 'Notifications enabled ✓';
                    status.style.color = 'green';
                } else {
                    status.textContent = 'Failed to subscribe';
                    status.style.color = 'red';
                }
            }
        } catch (error) {
            console.error('Error toggling notifications:', error);
            status.textContent = 'Error: ' + error.message;
            status.style.color = 'red';
        }
    }
    
    // Update button state on load
    async function updateButtonState() {
        const button = document.getElementById('notif-btn');
        const status = document.getElementById('notif-status');
        
        if (await pushNotifications.isSubscribed()) {
            button.textContent = '📭 Disable Notifications';
            status.textContent = 'Notifications enabled ✓';
            status.style.color = 'green';
        }
    }
    
    // Check status when page loads
    document.addEventListener('DOMContentLoaded', updateButtonState);
</script>
{% endblock %}
```

## Example 5: Send Targeted Notification to Specific User Groups

### Custom Helper Function

```python
# nog_app/nogoff/push_service.py - Add this method to PushNotificationService

def send_notification_to_groups(
    self,
    title: str,
    body: str,
    notification_type: str = "notification",
    groups: list = None,
    options: Optional[Dict] = None
) -> Dict:
    """
    Send notification to users in specific groups
    
    Args:
        title: Notification title
        body: Notification message
        notification_type: Type of notification
        groups: List of user IDs to target
        options: Additional notification options
        
    Returns:
        Results dictionary
    """
    from .models import User
    
    if groups is None:
        groups = []
    
    users = User.objects.filter(id__in=groups)
    
    results = {}
    for user in users:
        results[user.id] = self.send_notification(
            user, title, body, notification_type, options
        )
    
    return results

# Usage example:
def send_admin_alert(request):
    from .models import User
    from .push_service import push_service
    
    admin_users = User.objects.filter(is_admin=True)
    admin_ids = list(admin_users.values_list('id', flat=True))
    
    results = push_service.send_notification_to_groups(
        title="Admin Alert",
        body="A new event has been created",
        notification_type="admin_alert",
        groups=admin_ids
    )
    
    return JsonResponse(results)
```

## Example 6: Send Notification with Custom Data

### Enhanced Notification with Click Action

```python
# nog_app/nogoff/views.py

def notify_with_action(user, event):
    """Send notification that links to voting page when clicked"""
    from .push_service import push_service
    
    push_service.send_notification(
        user=user,
        title=f"Vote: {event.name}",
        body="Tap to vote now",
        notification_type="voting_prompt",
        options={
            "icon": "/static/images/voting-icon.png",
            "badge": "/static/images/badge.png",
            "tag": f"voting-{event.id}",
            "requireInteraction": True,  # Keep notification visible
            "data": {
                "url": f"/event/{event.id}",  # URL to open on click
                "event_id": event.id,
            }
        }
    )
```

## Example 7: Admin Command to Send Bulk Notifications

### Create Event-Specific Notification Command

```python
# nogoff/management/commands/notify_about_event.py

from django.core.management.base import BaseCommand
from nogoff.models import Event, User
from nogoff.push_service import push_service

class Command(BaseCommand):
    help = 'Send notifications about an event to all users'

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int, help='Event ID')
        parser.add_argument(
            '--type',
            type=str,
            default='event_notification',
            help='Notification type'
        )

    def handle(self, *args, **options):
        try:
            event = Event.objects.get(pk=options['event_id'])
            users = User.objects.all()
            
            self.stdout.write(f"Sending notifications for event: {event.name}")
            
            results = push_service.send_notification_to_all_users(
                title=f"📢 {event.name}",
                body="Voting is now open!",
                notification_type=options['type'],
                users=users
            )
            
            # Count successes and failures
            total = sum(1 for r in results.values() if isinstance(r, dict))
            successes = sum(
                1 for r in results.values() 
                if isinstance(r, dict) and r.get('status') == 'sent'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent notifications: {successes}/{total} successful'
                )
            )
            
        except Event.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Event not found')
            )
```

Usage:
```bash
python manage.py notify_about_event 1 --type event_start
```

## Example 8: Monitor Notification Delivery

### Analytics View

```python
# nogoff/views.py

from django.db.models import Count
from django.http import JsonResponse
from .push_models import PushNotificationLog

def notification_stats(request):
    """Get notification delivery statistics"""
    
    stats = {
        "total_sent": PushNotificationLog.objects.filter(
            status="sent"
        ).count(),
        "total_failed": PushNotificationLog.objects.filter(
            status="failed"
        ).count(),
        "by_type": PushNotificationLog.objects.values(
            'notification_type'
        ).annotate(count=Count('id')),
        "recent_failures": list(
            PushNotificationLog.objects.filter(
                status="failed"
            ).values('title', 'error_message', 'created_at')[:10]
        )
    }
    
    return JsonResponse(stats)
```

## Example 9: Clean Up Inactive Subscriptions

### Maintenance Task

```python
# nogoff/management/commands/cleanup_subscriptions.py

from django.core.management.base import BaseCommand
from nogoff.push_models import PushSubscription

class Command(BaseCommand):
    help = 'Remove inactive or old push subscriptions'

    def handle(self, *args, **options):
        from datetime import timedelta
        from django.utils import timezone
        
        # Remove subscriptions inactive for 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = PushSubscription.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted_count} old inactive subscriptions'
            )
        )
```

Usage:
```bash
python manage.py cleanup_subscriptions
```

## Example 10: Error Handling and Logging

### Robust Notification Sending with Retry

```python
# nogoff/push_service.py - Enhanced send_notification

def send_notification_with_retry(
    self,
    user,
    title,
    body,
    notification_type="notification",
    max_retries=3
):
    """Send notification with automatic retry on failure"""
    import time
    
    for attempt in range(max_retries):
        try:
            result = self.send_notification(
                user, title, body, notification_type
            )
            
            if any(
                r.get("status") == "sent" 
                for r in result.values() 
                if isinstance(r, dict)
            ):
                return result
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Retrying notification in {wait_time}s (attempt {attempt + 1})"
                )
                time.sleep(wait_time)
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt == max_retries - 1:
                raise
    
    return {"error": "Max retries exceeded"}
```

---

These examples should give you a good starting point for implementing push notifications in various scenarios throughout your NogApp!
