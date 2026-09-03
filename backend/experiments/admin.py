from django.contrib import admin

from .models import Deposit, ExperimentAssignment, FundingMethod, User, WebhookEvent


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "country", "created_at", "kyc_status"]
    list_filter = ["country", "kyc_status"]
    search_fields = ["id", "email"]


@admin.register(FundingMethod)
class FundingMethodAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "kind", "currency", "settlement_hours", "fee_pct"]


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "method", "amount_usd", "status", "created_at", "completed_at"]
    list_filter = ["status", "method"]
    search_fields = ["id", "user__id"]


@admin.register(ExperimentAssignment)
class ExperimentAssignmentAdmin(admin.ModelAdmin):
    list_display = ["user", "variant", "assigned_at"]
    list_filter = ["variant"]
    search_fields = ["user__id"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "type", "deposit_id", "occurred_at", "received_at"]
    list_filter = ["type"]
    search_fields = ["event_id", "deposit_id", "user_id"]
