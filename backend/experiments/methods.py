from .models import FundingMethod


def available_methods_for(country: str) -> list[FundingMethod]:
    """16 rows total — filtering in Python is simpler and just as fast as
    fighting JSONField array-containment queries for this size of table."""
    return [m for m in FundingMethod.objects.all() if country in m.countries or "*" in m.countries]


def recommend_method(country: str, available: list[FundingMethod]) -> FundingMethod:
    """What variant B shows as *the* method. Preference order: a local
    transfer for the user's own country (cheapest, usually fastest) beats a
    regional one (e.g. SEPA for EU countries) beats picking whatever's
    cheapest/fastest among what's left."""
    local = next((m for m in available if m.kind == "local_transfer"), None)
    if local:
        return local

    regional = next((m for m in available if m.kind == "bank_transfer" and "*" not in m.countries), None)
    if regional:
        return regional

    return min(available, key=lambda m: (m.fee_pct, m.settlement_hours, m.id))
