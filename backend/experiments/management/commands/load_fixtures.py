import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from experiments.models import Deposit, FundingMethod, User


class Command(BaseCommand):
    help = (
        "Loads users.json, funding_methods.json and deposits_historicos.json "
        "from DATA_DIR. Safe to run as many times as needed: each row is "
        "upserted (update_or_create), never duplicated."
    )

    def handle(self, *args, **options):
        self._load_users()
        self._load_funding_methods()
        self._load_deposits_historicos()

    def _read(self, filename):
        path = settings.DATA_DIR / filename
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_users(self):
        rows = self._read("users.json")
        for row in rows:
            User.objects.update_or_create(
                id=row["id"],
                defaults={
                    "email": row["email"],
                    "country": row["country"],
                    "created_at": parse_datetime(row["created_at"]),
                    "kyc_status": row["kyc_status"],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"users: {len(rows)}"))

    def _load_funding_methods(self):
        rows = self._read("funding_methods.json")
        for row in rows:
            FundingMethod.objects.update_or_create(
                id=row["id"],
                defaults={
                    "name": row["name"],
                    "kind": row["kind"],
                    "currency": row["currency"],
                    "countries": row["countries"],
                    "settlement_hours": row["settlement_hours"],
                    "fee_pct": row["fee_pct"],
                },
            )
        self.stdout.write(self.style.SUCCESS(f"funding_methods: {len(rows)}"))

    def _load_deposits_historicos(self):
        rows = self._read("deposits_historicos.json")
        for row in rows:
            Deposit.objects.update_or_create(
                id=row["id"],
                defaults={
                    "user_id": row["user_id"],
                    "method_id": row["method_id"],
                    "amount_usd": row["amount_usd"],
                    "status": row["status"],
                    "created_at": parse_datetime(row["created_at"]),
                    "completed_at": parse_datetime(row["completed_at"]),
                },
            )
        self.stdout.write(self.style.SUCCESS(f"deposits_historicos: {len(rows)}"))
