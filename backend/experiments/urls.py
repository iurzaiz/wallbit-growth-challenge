from django.urls import path

from . import views

urlpatterns = [
    path("funding-screen", views.FundingScreenView.as_view(), name="funding-screen"),
    path("webhooks/deposits", views.DepositWebhookView.as_view(), name="webhook-deposits"),
    path("events", views.TrackEventView.as_view(), name="track-event"),
    path("experiment/results", views.ExperimentResultsView.as_view(), name="experiment-results"),
    path("users", views.UserListView.as_view(), name="user-list"),
]
