"""
Management command that runs check_voting_reminders on a fixed interval,
forever, until the process receives SIGTERM/SIGINT (e.g. `docker stop`).
Usage: python manage.py run_reminder_scheduler [--interval SECONDS]
"""

import logging
import signal
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("nogoff")


class Command(BaseCommand):
    help = "Run check_voting_reminders on a loop until stopped"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Seconds to wait between checks (default: 60)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        self._running = True

        def _stop(signum, frame):
            self._running = False

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

        self.stdout.write(
            self.style.SUCCESS(
                f"Voting reminder scheduler started (checking every {interval}s)"
            )
        )

        while self._running:
            try:
                call_command("check_voting_reminders")
            except Exception:
                logger.exception("Error running check_voting_reminders")

            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

        self.stdout.write("Voting reminder scheduler stopped")
