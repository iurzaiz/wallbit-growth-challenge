from django.db import models


class User(models.Model):
    """Mirrors data/users.json. Not Django's auth model — there's no login
    in this exercise, this is just the business entity."""

    class KycStatus(models.TextChoices):
        APPROVED = "approved", "Approved"
        PENDING = "pending", "Pending"
        REJECTED = "rejected", "Rejected"

    id = models.CharField(max_length=32, primary_key=True)
    email = models.EmailField()
    country = models.CharField(max_length=2)
    created_at = models.DateTimeField()
    kyc_status = models.CharField(max_length=16, choices=KycStatus.choices)

    def __str__(self):
        return self.id


class ExperimentAssignment(models.Model):
    """One row per user who ever hit the funding screen. Created on first
    visit and never changed afterwards — that's what makes the variant
    sticky. See assignment.py for how the variant itself is picked."""

    class Variant(models.TextChoices):
        A = "A", "A - full list"
        B = "B", "B - recommended method"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="experiment_assignment"
    )
    variant = models.CharField(max_length=1, choices=Variant.choices)
    assigned_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user_id}:{self.variant}"


class FundingMethod(models.Model):
    """Mirrors data/funding_methods.json."""

    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=32)
    currency = models.CharField(max_length=8)
    countries = models.JSONField(help_text='List of ISO2 country codes, or ["*"] if it applies everywhere.')
    settlement_hours = models.PositiveIntegerField()
    fee_pct = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.id


class Deposit(models.Model):
    """One row per deposit_id. Populated from deposits_historicos.json (all
    with status=completed) and from the provider's webhooks during the
    experiment."""

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.CharField(max_length=32, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deposits")
    method = models.ForeignKey(FundingMethod, on_delete=models.PROTECT, related_name="deposits")
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices)
    currency = models.CharField(max_length=8, blank=True)
    country = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.id
