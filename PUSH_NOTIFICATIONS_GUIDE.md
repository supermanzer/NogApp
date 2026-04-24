# Push Notifications Implementation Guide for NogApp

## Overview
This guide explains how to implement Web Push Notifications in your Django NogApp using the Push API. Push notifications allow you to send timely messages to users even when they're not actively using your application.

## Implementation Summary

The implementation includes:
1. **Backend**: Django models, service layer, and API endpoints
2. **Frontend**: Service Worker and JavaScript client for subscription management
3. **Database**: Models to store subscriptions and notification logs
4. **Admin**: Django admin interface for managing notifications

## Components Created

### Backend Files

#### 1. `nogoff/push_models.py`
Contains two models:
- **PushSubscription**: Stores user push notification subscriptions
- **PushNotificationLog**: Logs all push notifications sent

#### 2. `nogoff/push_service.py`
Main service class `PushNotificationService` that:
- Registers/unregisters push subscriptions
- Sends notifications to single or multiple users
- Handles VAPID key configuration
- Manages invalid subscriptions

#### 3. `nogoff/push_views.py`
API endpoints for:
- `POST /api/push/subscribe/` - Register a subscription
- `POST /api/push/unsubscribe/` - Unregister a subscription
- `GET /api/push/public-key/` - Get VAPID public key

#### 4. `nogoff/management/commands/send_push_notification.py`
Management command to send notifications:
```bash
python manage.py send_push_notification --title "Title" --body "Message"
python manage.py send_push_notification --title "Title" --body "Message" --user-id 1
```

### Frontend Files

#### 1. `nogoff/static/js/service-worker.js`
Service Worker that:
- Listens for push events
- Displays notifications
- Handles notification clicks

#### 2. `nogoff/static/js/push-notifications.js`
JavaScript class `PushNotificationManager` that:
- Initializes push notifications
- Manages subscriptions
- Requests notification permissions
- Communicates with backend API

### Configuration Files Updated

#### 1. `nog_app/settings.py`
Added VAPID key configuration:
```python
PUSH_VAPID_PUBLIC_KEY = os.environ.get("PUSH_VAPID_PUBLIC_KEY")
PUSH_VAPID_PRIVATE_KEY = os.environ.get("PUSH_VAPID_PRIVATE_KEY")
PUSH_VAPID_EMAIL = os.environ.get("PUSH_VAPID_EMAIL", "admin@example.com")
```

#### 2. `nogoff/urls.py`
Added push notification API endpoints

#### 3. `nogoff/templates/nogoff/base.html`
Added push-notifications.js script loading

#### 4. `nogoff/admin.py`
Added Django admin interfaces for managing subscriptions and logs

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install pywebpush cryptography
```

Or if using Docker:
```bash
docker compose up -d --build
```

### Step 2: Generate VAPID Keys

Generate VAPID keys (needed for push notifications):

```python
# Run this in Python shell
from pywebpush import generate_vapid_keys

vapid_keys = generate_vapid_keys()
print(f"Public Key: {vapid_keys['public_key']}")
print(f"Private Key: {vapid_keys['private_key']}")
```

### Step 3: Set Environment Variables

Add to your `.env` file:
```
PUSH_VAPID_PUBLIC_KEY=<your_public_key>
PUSH_VAPID_PRIVATE_KEY=<your_private_key>
PUSH_VAPID_EMAIL=your-email@example.com
```

### Step 4: Run Migrations

```bash
python manage.py makemigrations nogoff
python manage.py migrate
```

This creates the `PushSubscription` and `PushNotificationLog` tables.

### Step 5: Static Files

Ensure you have icons for notifications. Create or add:
- `/nogoff/static/images/icon.png` - Notification icon (192x192 or larger)
- `/nogoff/static/images/badge.png` - Notification badge (72x72 or larger)

## Usage

### Frontend: Subscribing to Notifications

```javascript
// Automatically initialized on page load
// The pushNotifications object is globally available

// Request permission first
await pushNotifications.requestPermission();

// Subscribe to notifications
const success = await pushNotifications.subscribe();
if (success) {
    console.log('Successfully subscribed to push notifications');
}

// Check subscription status
const isSubscribed = await pushNotifications.isSubscribed();

// Unsubscribe
await pushNotifications.unsubscribe();
```

### Backend: Sending Notifications

#### Using Management Command

```bash
# Send to all users
python manage.py send_push_notification \
    --title "Voting Event Started" \
    --body "Vote for your favorite nog!" \
    --type "event_notification"

# Send to specific user
python manage.py send_push_notification \
    --title "Personal Message" \
    --body "Your votes have been recorded" \
    --type "vote_confirmation" \
    --user-id 1
```

#### Using Python Code

```python
from nogoff.models import User
from nogoff.push_service import push_service

# Send to a single user
user = User.objects.get(pk=1)
push_service.send_notification(
    user=user,
    title="Voting Started",
    body="Time to vote for your favorite nog!",
    notification_type="event_notification"
)

# Send to all users
all_users = User.objects.all()
results = push_service.send_notification_to_all_users(
    title="Important Update",
    body="New voting event has been created",
    notification_type="broadcast",
    users=all_users
)
```

#### In Django Views

```python
from nogoff.push_service import push_service
from .models import Event, User

def my_view(request):
    event = Event.objects.get(pk=1)
    
    # Notify all users about voting
    results = push_service.send_notification_to_all_users(
        title="Vote Now!",
        body=f"Voting for '{event.name}' is now open",
        notification_type="voting_started",
        users=User.objects.all()
    )
    
    return JsonResponse(results)
```

#### With Scheduling (Using Celery - Optional)

For scheduling notifications, you can integrate with Celery:

```python
from celery import shared_task
from nogoff.push_service import push_service
from .models import Event, User

@shared_task
def send_event_reminder(event_id):
    event = Event.objects.get(pk=event_id)
    users = User.objects.all()
    
    push_service.send_notification_to_all_users(
        title="Reminder",
        body=f"'{event.name}' is happening soon!",
        notification_type="event_reminder",
        users=users
    )
```

## Admin Interface

Visit `/admin/` and you'll find:

1. **Push Subscriptions**
   - View all user subscriptions
   - See creation dates and active status
   - Search by user name
   - Deactivate subscriptions if needed

2. **Push Notification Logs**
   - View history of all sent notifications
   - Filter by status (pending, sent, failed)
   - Search by title, body, or user
   - Debug failed notifications

## Browser Support

Push API is supported in:
- Chrome/Edge 50+
- Firefox 44+
- Opera 37+
- Samsung Internet 5+

**Not supported in:**
- Safari
- IE

## Notification Lifecycle

1. **Client subscribes**: User grants permission and browser generates subscription
2. **Backend receives**: Subscription data stored in database
3. **Backend sends**: Admin sends notification via management command or API
4. **Service Worker receives**: Push event triggers notification display
5. **User sees**: OS displays notification
6. **User clicks**: Service Worker handles click and navigates to app

## Error Handling

The system automatically handles:
- Invalid/expired subscriptions (marks as inactive)
- Failed network requests (logs error)
- Missing VAPID keys (warning logged)
- Browser compatibility (graceful degradation)

## Security Considerations

1. **VAPID Keys**: Keep private key secure in `.env` file
2. **CSRF Protection**: All subscription endpoints have CSRF tokens
3. **User Validation**: Subscriptions tied to user session
4. **Rate Limiting**: Consider adding rate limiting to prevent abuse

## Troubleshooting

### Notifications not appearing
- Check browser console for errors
- Verify Service Worker is registered (DevTools > Application)
- Confirm notification permission is granted
- Verify VAPID keys are set correctly

### "VAPID keys not configured" warning
- Generate VAPID keys and add to `.env`
- Restart Django server
- Verify environment variables are loaded

### Service Worker not updating
- Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)
- Clear browser cache
- Unregister old Service Worker in DevTools

### Subscriptions not saving
- Check database migrations ran: `python manage.py migrate`
- Verify PushSubscription model in admin
- Check browser console for network errors

## Testing Push Notifications

### Chrome DevTools Method
1. Open DevTools (F12)
2. Go to Application > Service Workers
3. Find your service worker
4. Check the "Offline" box
5. Click "Push" button to simulate push

### Using curl (for backend testing)
```bash
curl -X POST http://localhost:8000/api/push/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{"subscription": {"endpoint": "...", "keys": {...}}}'
```

## Production Considerations

1. **Database**: Ensure proper backups of subscription data
2. **Monitoring**: Track notification delivery rates
3. **Cleanup**: Periodically clean up invalid subscriptions
4. **Logging**: Monitor push_service logs for errors
5. **HTTPS**: Required for Service Workers in production

## Next Steps

1. **Customize notifications**: Add custom icons and styling
2. **Add scheduling**: Use Celery for timed notifications
3. **Analytics**: Track notification engagement
4. **User preferences**: Let users control notification types
5. **A/B testing**: Test different notification messages

## Example Use Cases

### Event Reminders
```python
@shared_task
def send_event_reminders():
    from datetime import timedelta
    from django.utils import timezone
    
    upcoming = Event.objects.filter(
        event_date__lte=timezone.now() + timedelta(hours=1),
        event_date__gt=timezone.now()
    )
    
    for event in upcoming:
        push_service.send_notification_to_all_users(
            title="Event Starting Soon",
            body=f"{event.name} starts in 1 hour",
            notification_type="event_reminder"
        )
```

### Vote Confirmation
```python
def vote(request, nog_id):
    # ... voting logic ...
    
    # Send confirmation
    push_service.send_notification(
        user=request.device_user,
        title="Vote Recorded",
        body="Your vote has been successfully recorded",
        notification_type="vote_confirmation"
    )
    
    return JsonResponse({"status": "success"})
```

### Broadcast Announcements
```python
# Management command: send_push_notification --title "Nog Event Today!" --body "Vote now"
# Or programmatically:
push_service.send_notification_to_all_users(
    title="Nog Event Today!",
    body="The annual Nog competition is starting",
    notification_type="announcement"
)
```
