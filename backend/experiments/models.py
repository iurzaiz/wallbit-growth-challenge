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


class WebhookEvent(models.Model):
    """Raw log of every webhook received, one row per event_id. Only for
    auditing/debugging — the experiment result is read from Deposit, not
    from here. event_id as primary key is what makes duplicate delivery
    (the provider's at-least-once guarantee) a no-op: a retried event_id
    just fails to insert a second row."""

    class Type(models.TextChoices):
        RECEIVED = "deposit.received", "Received"
        COMPLETED = "deposit.completed", "Completed"
        FAILED = "deposit.failed", "Failed"

    event_id = models.CharField(max_length=32, primary_key=True)
    type = models.CharField(max_length=32, choices=Type.choices)
    occurred_at = models.DateTimeField()
    deposit_id = models.CharField(max_length=32)
    user_id = models.CharField(max_length=32)
    method_id = models.CharField(max_length=32)
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8)
    country = models.CharField(max_length=2)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_id


class TrackingEvent(models.Model):
    """One row per funnel step. Lets us see *where* people drop off between
    variants, not just the final conversion number — see PLAN.md #3.
    `variant` is denormalized from the user's assignment at record time so
    funnel queries don't need a join. `occurred_at` defaults to now but can
    be backdated (see tracking.py / simulate_visits)."""

    class EventName(models.TextChoices):
        EXPERIMENT_ASSIGNED = "experiment_assigned", "Experiment assigned"
        FUNDING_SCREEN_VIEWED = "funding_screen_viewed", "Funding screen viewed"
        OTHER_METHODS_EXPANDED = "other_methods_expanded", "Other methods expanded"
        METHOD_SELECTED = "method_selected", "Method selected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tracking_events")
    event_name = models.CharField(max_length=32, choices=EventName.choices)
    variant = models.CharField(max_length=1, blank=True)
    metadata = models.JSONField(blank=True, default=dict)
    occurred_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user_id}:{self.event_name}"


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
