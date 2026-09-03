from django.utils import timezone
from rest_framework import serializers

from .assignment import variant_for
from .methods import available_methods_for, recommend_method
from .models import ExperimentAssignment, FundingMethod, User


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
