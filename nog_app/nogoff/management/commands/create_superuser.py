"""
Django management command to create a superuser from environment variables.
Useful for automated deployments where interactive input isn't available.

Usage:
    python manage.py create_superuser

Environment variables required:
    DJANGO_SUPERUSER_USERNAME - Username for the superuser
    DJANGO_SUPERUSER_EMAIL - Email for the superuser
    DJANGO_SUPERUSER_PASSWORD - Password for the superuser
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    help = "Create a Django superuser from environment variables (for automated deployments)"

    def handle(self, *args, **options):
        User = get_user_model()

        # Get credentials from environment variables
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        # Validate all required variables are set
        if not all([username, email, password]):
            self.stdout.write(
                self.style.WARNING(
                    "Superuser creation skipped. Set DJANGO_SUPERUSER_USERNAME, "
                    "DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD "
                    "environment variables to create a superuser."
                )
            )
            return

        # Check if superuser already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Superuser with username "{username}" already exists. Skipping creation.'
                )
            )
            return

        # Create the superuser
        try:
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{username}" with email "{email}"'
                )
            )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create superuser: {str(e)}")
            )
