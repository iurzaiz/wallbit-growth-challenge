from django.db import models


class User(models.Model):
    """Mirrors data/users.json. Not Django's auth model — there's no login
    in this exercise, this is just the business entity."""

    KYC_APPROVED = "approved"
    KYC_PENDING = "pending"
    KYC_REJECTED = "rejected"
    KYC_STATUS_CHOICES = [
        (KYC_APPROVED, "Approved"),
        (KYC_PENDING, "Pending"),
        (KYC_REJECTED, "Rejected"),
    ]

    id = models.CharField(max_length=32, primary_key=True)
    email = models.EmailField()
    country = models.CharField(max_length=2)
    created_at = models.DateTimeField()
    kyc_status = models.CharField(max_length=16, choices=KYC_STATUS_CHOICES)

    def __str__(self):
        return self.id


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

    STATUS_RECEIVED = "received"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RECEIVED, "Received"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.CharField(max_length=32, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deposits")
    method = models.ForeignKey(FundingMethod, on_delete=models.PROTECT, related_name="deposits")
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    currency = models.CharField(max_length=8, blank=True)
    country = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.id
