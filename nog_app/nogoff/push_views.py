"""
API views for handling push notification subscriptions
"""

import json
import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .push_service import push_service

logger = logging.getLogger("nogoff")


@require_POST
@csrf_exempt
def subscribe_to_push(request: HttpRequest) -> JsonResponse:
    """
    Handle push notification subscription

    Expects JSON body with:
    {
        "subscription": {
            "endpoint": "...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
    }
    """
    try:
        user = getattr(request, "device_user", None)
        if not user:
            return JsonResponse({"error": "User not found"}, status=401)

        body = json.loads(request.body)
        subscription_json = body.get("subscription")

        if not subscription_json:
            return JsonResponse(
                {"error": "Invalid subscription data"}, status=400
            )

        # Register the subscription
        push_service.register_subscription(
            user=user,
            subscription_json=subscription_json,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        logger.info(f"Push subscription registered for user {user.name}")

        return JsonResponse(
            {
                "status": "success",
                "message": "Push subscription registered successfully",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception("Error registering push subscription")
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_exempt
def unsubscribe_from_push(request: HttpRequest) -> JsonResponse:
    """
    Handle push notification unsubscription

    Expects JSON body with:
    {
        "subscription": {
            "endpoint": "...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
    }
    """
    try:
        user = getattr(request, "device_user", None)
        if not user:
            return JsonResponse({"error": "User not found"}, status=401)

        body = json.loads(request.body)
        subscription_json = body.get("subscription")

        if not subscription_json:
            return JsonResponse(
                {"error": "Invalid subscription data"}, status=400
            )

        # Unregister the subscription
        success = push_service.unregister_subscription(
            user=user, subscription_json=subscription_json
        )

        if success:
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Push subscription removed successfully",
                }
            )
        else:
            return JsonResponse(
                {"status": "not_found", "message": "Subscription not found"},
                status=404,
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.exception("Error unregistering push subscription")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_push_public_key(request: HttpRequest) -> JsonResponse:
    """
    Get the public VAPID key for client-side subscription
    """
    try:
        public_key = push_service.vapid_public_key

        if not public_key:
            return JsonResponse(
                {"error": "Push notifications not configured"}, status=503
            )

        return JsonResponse({"status": "success", "publicKey": public_key})

    except Exception as e:
        logger.exception("Error getting push public key")
        return JsonResponse({"error": str(e)}, status=500)
