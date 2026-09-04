import json
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from experiments.assignment import variant_for
from experiments.models import ExperimentAssignment, User


class Command(BaseCommand):
    help = (
        "Backdates a funding-screen visit for every user in scenario.json, "
        "shortly before their first webhook event. Run this before "
        "simulate_provider.py: otherwise every assignment happens through "
        "the webhook's fallback (assigned_at = webhook time), and the "
        "conversion window ends up measuring 'did people who were already "
        "depositing keep depositing' instead of the effect of the variant."
    )

    def add_arguments(self, parser):
        parser.add_argument("--scenario", default=str(settings.SCENARIO_PATH))

    def handle(self, *args, **options):
        with open(options["scenario"], encoding="utf-8") as f:
            events = json.load(f)["events"]

        first_seen_at = {}
        for event in events:
            user_id = event["data"]["user_id"]
            occurred_at = parse_datetime(event["occurred_at"])
            if user_id not in first_seen_at or occurred_at < first_seen_at[user_id]:
                first_seen_at[user_id] = occurred_at

        created = 0
        for user_id, first_event_at in first_seen_at.items():
            user = User.objects.filter(pk=user_id).first()
            if user is None:
                continue

            # Deterministic per user, so re-running this command is a no-op
            # (get_or_create) rather than a source of drifting timestamps.
            rng = random.Random(user_id)
            visited_at = first_event_at - timedelta(minutes=rng.randint(5, 180))

            _, was_created = ExperimentAssignment.objects.get_or_create(
                user=user,
                defaults={"variant": variant_for(user.id), "assigned_at": visited_at},
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(f"scenario users: {len(first_seen_at)}, newly assigned: {created}"))
