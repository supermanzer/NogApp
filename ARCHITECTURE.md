# Push Notifications Architecture & Flow Diagrams

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER'S BROWSER                                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              HTML Page (base.html)                         │  │
│  │  - Loads push-notifications.js script                      │  │
│  │  - Auto-initializes on page load                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │    PushNotificationManager (push-notifications.js)         │  │
│  │  ├─ init() - Register Service Worker                       │  │
│  │  ├─ subscribe() - Get subscription & send to backend       │  │
│  │  ├─ unsubscribe() - Remove subscription                    │  │
│  │  └─ requestPermission() - Ask for browser permission      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │           Service Worker (service-worker.js)               │  │
│  │  ├─ Runs in background                                     │  │
│  │  ├─ Listens for 'push' events                              │  │
│  │  └─ Displays notifications to user                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ↕
                    (HTTP/HTTPS API Calls)
                              ↕
┌──────────────────────────────────────────────────────────────────┐
│                    DJANGO BACKEND                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                 API Views (push_views.py)                  │  │
│  │  POST   /api/push/subscribe/      → register subscription  │  │
│  │  POST   /api/push/unsubscribe/    → remove subscription    │  │
│  │  GET    /api/push/public-key/     → get VAPID key         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │           Push Service (push_service.py)                   │  │
│  │  ├─ register_subscription() - Save to database             │  │
│  │  ├─ send_notification() - Sign & push via VAPID            │  │
│  │  └─ unregister_subscription() - Remove from database       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Database Models (push_models.py)              │  │
│  │  ├─ PushSubscription - Store endpoints & keys              │  │
│  │  └─ PushNotificationLog - Audit trail                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Django Admin Interface                         │  │
│  │  ├─ View/manage subscriptions                              │  │
│  │  ├─ View notification history                              │  │
│  │  └─ Debug failed notifications                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │            Management Commands                              │  │
│  │  python manage.py send_push_notification                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ↕
            (HTTPS Push API Protocol with VAPID)
                              ↕
┌──────────────────────────────────────────────────────────────────┐
│              BROWSER'S PUSH SERVICE (FCM/etc)                     │
│  - Receives signed push notification                             │
│  - Queues notification delivery                                  │
│  - Handles retries if user offline                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    (When user comes online)
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   SERVICE WORKER ACTIVATED                        │
│  - Receives push event from browser                              │
│  - Displays notification in OS notification center               │
│  - Handles user interaction                                      │
└──────────────────────────────────────────────────────────────────┘
```

## Subscription Flow (How Users Enable Notifications)

```
User Visits App
    │
    ↓
[base.html loads push-notifications.js]
    │
    ↓
PushNotificationManager.init()
    ├─ Register Service Worker
    │    └─ Service worker installed & ready
    │
    ├─ Fetch VAPID public key from backend
    │    └─ GET /api/push/public-key/
    │
    └─ Check if already subscribed
         └─ If yes: Show "Disable Notifications" button
         └─ If no: Show "Enable Notifications" button
    │
    ↓
User Clicks "Enable Notifications"
    │
    ↓
pushNotifications.requestPermission()
    │
    ├─ Browser prompts user
    │
    ↓ (User clicks "Allow")
    │
    ├─ Get notification permission granted
    │
    ↓
pushNotifications.subscribe()
    │
    ├─ Call PushManager.subscribe()
    │    └─ Browser generates subscription object
    │       (includes endpoint, p256dh key, auth key)
    │
    ├─ Send subscription to backend
    │    └─ POST /api/push/subscribe/
    │       └─ JSON: { "subscription": {...} }
    │
    ↓
Backend receives subscription
    │
    ├─ push_service.register_subscription()
    │    └─ Store in database
    │       └─ PushSubscription model
    │
    ├─ Return success response
    │
    ↓
Frontend shows "✓ Notifications enabled"
    │
    ↓
User is now subscribed and ready to receive notifications!
```

## Notification Send Flow (How Notifications Are Delivered)

```
Admin/View wants to send notification
    │
    ├─ Option A: Use management command
    │    python manage.py send_push_notification \
    │      --title "..." --body "..." --type "..."
    │
    ├─ Option B: Call from Django view
    │    push_service.send_notification(user, title, body, ...)
    │
    └─ Option C: Use Django admin
         └─ Not yet implemented, but can be added
    │
    ↓
push_service.send_notification()
    │
    ├─ Query database for user's subscriptions
    │    └─ SELECT * FROM PushSubscription WHERE user=X AND is_active=True
    │
    ├─ Build notification payload
    │    └─ { "notification": { "title": "...", "body": "...", ... } }
    │
    ├─ For each subscription:
    │    │
    │    ├─ Sign payload with VAPID private key
    │    │    └─ Creates secure cryptographic signature
    │    │
    │    ├─ Call pywebpush.webpush()
    │    │    └─ Sends to subscription.endpoint via HTTPS
    │    │       (Push Service URL, e.g., Google FCM, Mozilla APNs)
    │    │
    │    ├─ If successful (200 OK):
    │    │    ├─ Log: status="sent"
    │    │    └─ Create PushNotificationLog entry
    │    │
    │    └─ If failed:
    │         ├─ Check error code
    │         │
    │         ├─ If 410 (invalid endpoint):
    │         │    └─ Mark subscription as inactive (is_active=False)
    │         │       (User probably uninstalled browser or cleared data)
    │         │
    │         ├─ Log: status="failed", error_message="..."
    │         └─ Create PushNotificationLog entry
    │
    ↓
Browser's Push Service receives signed notification
    │
    ├─ Verifies VAPID signature
    │
    ├─ Checks if endpoint matches subscription
    │
    └─ Queues notification for delivery
    │
    ↓
When browser/user comes online:
    │
    ├─ Push Service delivers notification to browser
    │
    ├─ Service Worker receives 'push' event
    │    └─ (Even if page is closed!)
    │
    ├─ service-worker.js handles event
    │    │
    │    ├─ Parses notification data
    │    │
    │    └─ self.registration.showNotification()
    │       └─ Displays in OS notification center
    │
    ↓
User sees notification!
    │
    ├─ User clicks notification
    │    └─ notificationclick event in service worker
    │    └─ Opens app/website
    │
    └─ User dismisses
         └─ Notification disappears
```

## Database Schema

```
┌─────────────────────────────────────┐
│      PushSubscription               │
├─────────────────────────────────────┤
│ id (PK)                             │
│ user_id (FK → User)                 │
│ subscription_json (JSON)            │
│   ├─ endpoint: "https://..."        │
│   └─ keys:                          │
│       ├─ p256dh: "..."              │
│       └─ auth: "..."                │
│ user_agent (CharField)              │
│ created_at (DateTime)               │
│ updated_at (DateTime)               │
│ is_active (Boolean)                 │
└─────────────────────────────────────┘
           ↑
           │ (Foreign Key)
           │
    ┌──────────────┐
    │    User      │
    ├──────────────┤
    │ id (PK)      │
    │ name         │
    │ is_admin     │
    │ has_voted    │
    │ last_login   │
    └──────────────┘

┌──────────────────────────────────────┐
│    PushNotificationLog               │
├──────────────────────────────────────┤
│ id (PK)                              │
│ user_id (FK → User)                  │
│ title (CharField)                    │
│ body (TextField)                     │
│ notification_type (CharField)        │
│ status (CharField)                   │
│   ├─ "pending"                       │
│   ├─ "sent"                          │
│   └─ "failed"                        │
│ error_message (TextField)            │
│ created_at (DateTime)                │
│ sent_at (DateTime, nullable)         │
└──────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  base.html → Push button UI                                  │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│               JAVASCRIPT CLIENT LAYER                        │
│  push-notifications.js → PushNotificationManager class       │
│  ├─ manages subscription state                              │
│  ├─ communicates with backend API                           │
│  └─ interacts with Service Worker                           │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                   SERVICE WORKER LAYER                       │
│  service-worker.js → Runs in background                     │
│  ├─ receives push events                                    │
│  ├─ displays notifications                                  │
│  └─ handles user interactions                               │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                   API LAYER (Django REST)                    │
│  push_views.py → Endpoints                                  │
│  ├─ POST /api/push/subscribe/                               │
│  ├─ POST /api/push/unsubscribe/                             │
│  └─ GET /api/push/public-key/                               │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                         │
│  push_service.py → PushNotificationService class            │
│  ├─ register_subscription()                                 │
│  ├─ unregister_subscription()                               │
│  ├─ send_notification()                                     │
│  └─ send_notification_to_all_users()                        │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                   DATA ACCESS LAYER                          │
│  push_models.py → Database models                           │
│  ├─ PushSubscription                                        │
│  └─ PushNotificationLog                                     │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│  ├─ nogoff_pushsubscription table                           │
│  └─ nogoff_pushnotificationlog table                        │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Sending a Notification

```
Step 1: Admin sends command
    python manage.py send_push_notification \
        --title "Voting Open" \
        --body "Vote now!" \
        --user-id 1

Step 2: Management command calls service
    push_service.send_notification(
        user=User(id=1),
        title="Voting Open",
        body="Vote now!",
        notification_type="voting_started"
    )

Step 3: Service retrieves subscriptions
    subscriptions = PushSubscription.objects.filter(
        user_id=1,
        is_active=True
    )
    # Returns: [
    #     {
    #         endpoint: "https://fcm.googleapis.com/...",
    #         keys: {p256dh: "...", auth: "..."}
    #     }
    # ]

Step 4: Service builds payload
    payload = {
        "notification": {
            "title": "Voting Open",
            "body": "Vote now!",
            "icon": "/static/images/icon.png",
            "badge": "/static/images/badge.png"
        }
    }

Step 5: Service signs with VAPID
    signed_push = webpush(
        subscription=subscription_json,
        data=json.dumps(payload),
        vapid_private_key=settings.PUSH_VAPID_PRIVATE_KEY,
        vapid_claims={"sub": "admin@example.com"}
    )

Step 6: Push Service receives (FCM/etc)
    POST https://fcm.googleapis.com/send
    Headers:
        Crypto-Key: p256ecdsa=<VAPID_PUBLIC_KEY>
        Authorization: WebPush <SIGNATURE>
    Body: <encrypted_payload>

Step 7: Browser/OS delivers
    Service Worker receives 'push' event
    ├─ Extracts notification data
    └─ Calls showNotification()

Step 8: User sees
    OS Notification:
    ┌─────────────────────────┐
    │ 📬 Voting Open          │
    │                         │
    │ Vote now!              │
    │                         │
    │ [Open]  [Dismiss]      │
    └─────────────────────────┘

Step 9: Logging
    PushNotificationLog created:
    {
        user_id: 1,
        title: "Voting Open",
        body: "Vote now!",
        notification_type: "voting_started",
        status: "sent",
        sent_at: "2024-12-04 15:30:00"
    }
```

## State Machine: Subscription Lifecycle

```
                        ┌──────────────┐
                        │   No Access  │
                        │    (Start)   │
                        └──────────────┘
                              ↓
                              │ (User clicks Enable)
                              ↓
                        ┌──────────────┐
                        │ Permission   │
                        │  Requested   │
                        └──────────────┘
                              ↓
                      ┌─────────────────┐
                  ╱─→ │ Denied       ├──╱─→ [End - No Access]
                 │    └─────────────────┘
                 │
           ┌─────┴────────────────┐
        (Allow)              (Block)
           │
           ↓
    ┌──────────────┐
    │ Subscribing  │
    └──────────────┘
           ↓
           │ (Send subscription to server)
           ↓
    ┌──────────────┐
    │ Subscribed   │ (is_active=True)
    │   (Active)   │
    └──────────────┘
           ↑  ↓
           │  │ (Invalid push response)
           │  └────────────┐
           │               ↓
           │        ┌──────────────┐
           └────←─ │ Unsubscribed │ (is_active=False)
                    │  (Inactive)  │
                    └──────────────┘
                           ↓
                           │ (User unsubscribes)
                           ↓
                    ┌──────────────┐
                    │ Deleted from │
                    │  Database    │
                    └──────────────┘
```

---

These diagrams show how the push notification system works from end-to-end. Refer to them when:
- Understanding the architecture
- Debugging issues
- Adding new features
- Explaining to team members
