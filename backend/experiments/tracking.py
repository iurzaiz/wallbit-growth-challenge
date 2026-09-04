from django.utils import timezone

from .models import TrackingEvent


def record(user, event_name, *, variant="", occurred_at=None, **metadata):
    return TrackingEvent.objects.create(
        user=user,
        event_name=event_name,
        variant=variant,
        occurred_at=occurred_at or timezone.now(),
        metadata=metadata,
    )
