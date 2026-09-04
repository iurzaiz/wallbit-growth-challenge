from collections import defaultdict
from datetime import timedelta

from .models import Deposit, ExperimentAssignment

CONVERSION_WINDOW = timedelta(days=7)


def compute_variant_results():
    """Assigned vs. converted per variant. "Converted" = a completed deposit
    for that user within 7 days of *assignment* (not signup) — see
    ENTREGA.md / PLAN.md for why the window is anchored there instead of
    the company's literal activation metric."""
    completed_at_by_user = defaultdict(list)
    for deposit in Deposit.objects.filter(status=Deposit.Status.COMPLETED):
        completed_at_by_user[deposit.user_id].append(deposit.completed_at)

    stats = {variant: {"assigned": 0, "converted": 0} for variant, _ in ExperimentAssignment.Variant.choices}

    for assignment in ExperimentAssignment.objects.all():
        bucket = stats[assignment.variant]
        bucket["assigned"] += 1

        window_end = assignment.assigned_at + CONVERSION_WINDOW
        converted = any(
            assignment.assigned_at <= completed_at <= window_end
            for completed_at in completed_at_by_user[assignment.user_id]
        )
        if converted:
            bucket["converted"] += 1

    return [
        {
            "variant": variant,
            "assigned": bucket["assigned"],
            "converted": bucket["converted"],
            "conversion_rate": bucket["converted"] / bucket["assigned"] if bucket["assigned"] else 0.0,
        }
        for variant, bucket in stats.items()
    ]
