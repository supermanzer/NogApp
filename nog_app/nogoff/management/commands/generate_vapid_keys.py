import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate VAPID key pair for push notifications"

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Public key: uncompressed EC point, base64url-encoded (no padding).
        # This is the format the browser's pushManager.subscribe() expects for
        # applicationServerKey, and what pywebpush sends in the VAPID header.
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()

        # Private key: PEM string. pywebpush's webpush() accepts this directly.
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        self.stdout.write(self.style.SUCCESS("Add these to your .env file:\n"))
        self.stdout.write(f"PUSH_VAPID_PUBLIC_KEY={pub_b64}")
        self.stdout.write(f'PUSH_VAPID_PRIVATE_KEY="{priv_pem}"')
        self.stdout.write(f"PUSH_VAPID_EMAIL=mailto:your@email.com")
