import hashlib

from .models import ExperimentAssignment


def variant_for(user_id: str) -> str:
    """Deterministic A/B split from the user_id: same input, same output,
    always — no need to store anything to know which group a user *would*
    land in. What we persist (ExperimentAssignment) is *when* they landed
    in it, not which variant, since that's recomputable at any time."""
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return ExperimentAssignment.Variant.A if int(digest, 16) % 2 == 0 else ExperimentAssignment.Variant.B
