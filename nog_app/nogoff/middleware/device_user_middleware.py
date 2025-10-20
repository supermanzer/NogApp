import hashlib
import uuid

from nogoff.models import User

from django.utils.deprecation import MiddlewareMixin

# NOTE: when using User-Agent, we do NOT set a cookie; the id is derived from the header.
DEVICE_PREFIX = "ua-"


class DeviceUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Get the User-Agent header (or fallback to REMOTE_ADDR if UA is missing)
        ua = request.META.get("HTTP_USER_AGENT", "").strip()
        fallback = request.META.get("REMOTE_ADDR", "").strip()
        source = ua or fallback or uuid.uuid4().hex

        # Create a deterministic short id by hashing the source
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        device_id = f"{DEVICE_PREFIX}{digest}"

        # Get or create the user based on the derived device id
        user, created = User.objects.get_or_create(name=device_id)

        # Optionally log the user in if integrating with Django auth:
        # login(request, user)

        # Attach device user to the request
        request.device_user = user

    def process_response(self, request, response):
        # No cookie is set when deriving device id from headers
        return response
