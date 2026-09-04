from django.urls import path

from . import views

urlpatterns = [
    path("funding-screen", views.FundingScreenView.as_view(), name="funding-screen"),
    path("webhooks/deposits", views.DepositWebhookView.as_view(), name="webhook-deposits"),
    path("experiment/results", views.ExperimentResultsView.as_view(), name="experiment-results"),
]
