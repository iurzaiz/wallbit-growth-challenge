from django.utils import timezone
from rest_framework import serializers

from .assignment import variant_for
from .methods import available_methods_for, recommend_method
from .models import Deposit, ExperimentAssignment, FundingMethod, User, WebhookEvent


class VariantResultSerializer(serializers.Serializer):
    variant = serializers.CharField()
    assigned = serializers.IntegerField()
    converted = serializers.IntegerField()
    conversion_rate = serializers.FloatField()


class FundingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingMethod
        fields = ["id", "name", "kind", "currency", "settlement_hours", "fee_pct"]


class FundingScreenSerializer(serializers.Serializer):
    """Doubles as input (user_id) and output. `.save()` assigns the variant
    if the user hasn't visited before (or is a no-op if they have), then
    `.data` renders the full screen payload from the result."""

    user_id = serializers.CharField(write_only=True)
    country = serializers.CharField(read_only=True)
    variant = serializers.CharField(read_only=True)
    assigned_at = serializers.DateTimeField(read_only=True)
    recommended_method_id = serializers.CharField(read_only=True, allow_null=True)
    methods = FundingMethodSerializer(many=True, read_only=True)

    def validate_user_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def create(self, validated_data):
        user = User.objects.get(pk=validated_data["user_id"])

        assignment, _ = ExperimentAssignment.objects.get_or_create(
            user=user,
            defaults={"variant": variant_for(user.id), "assigned_at": timezone.now()},
        )

        methods = available_methods_for(user.country)
        is_variant_b = assignment.variant == ExperimentAssignment.Variant.B
        recommended = recommend_method(user.country, methods) if is_variant_b else None

        return {
            "user_id": user.id,
            "country": user.country,
            "variant": assignment.variant,
            "assigned_at": assignment.assigned_at,
            "recommended_method_id": recommended.id if recommended else None,
            "methods": methods,
        }


class DepositWebhookDataSerializer(serializers.Serializer):
    deposit_id = serializers.CharField()
    user_id = serializers.CharField()
    method_id = serializers.CharField()
    amount_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    country = serializers.CharField()


class DepositWebhookSerializer(serializers.Serializer):
    """Mirrors the provider's payload (simulator/PROVIDER.md). `.save()`
    handles everything the provider warns about: duplicate event_id,
    duplicate deposit_id under a new event_id, and out-of-order delivery.
    See PLAN.md #4 for the reasoning."""

    _DEPOSIT_STATUS_BY_TYPE = {
        WebhookEvent.Type.RECEIVED: Deposit.Status.RECEIVED,
        WebhookEvent.Type.COMPLETED: Deposit.Status.COMPLETED,
        WebhookEvent.Type.FAILED: Deposit.Status.FAILED,
    }

    event_id = serializers.CharField()
    type = serializers.ChoiceField(choices=WebhookEvent.Type.choices)
    occurred_at = serializers.DateTimeField()
    data = DepositWebhookDataSerializer()

    def create(self, validated_data):
        event, created = WebhookEvent.objects.get_or_create(
            event_id=validated_data["event_id"],
            defaults={
                "type": validated_data["type"],
                "occurred_at": validated_data["occurred_at"],
                **validated_data["data"],
            },
        )
        if not created:
            # Same event_id we already logged — a provider retry. Nothing
            # left to do, the first delivery already applied it.
            return event

        self._apply(event)
        return event

    def _apply(self, event):
        user = User.objects.get(pk=event.user_id)

        # Fallback assignment: a webhook implies the user must have seen
        # their account details on the funding screen already, so if we
        # somehow never saw that visit, enter them into the experiment now.
        ExperimentAssignment.objects.get_or_create(
            user=user,
            defaults={"variant": variant_for(user.id), "assigned_at": event.occurred_at},
        )

        deposit = Deposit.objects.filter(pk=event.deposit_id).first()
        if deposit and deposit.status in (Deposit.Status.COMPLETED, Deposit.Status.FAILED):
            # Already terminal — a late/out-of-order event changes nothing.
            return

        status = self._DEPOSIT_STATUS_BY_TYPE[event.type]
        Deposit.objects.update_or_create(
            id=event.deposit_id,
            defaults={
                "user": user,
                "method_id": event.method_id,
                "amount_usd": event.amount_usd,
                "status": status,
                "currency": event.currency,
                "country": event.country,
                "created_at": deposit.created_at if deposit else event.occurred_at,
                "completed_at": event.occurred_at if status == Deposit.Status.COMPLETED else None,
            },
        )
