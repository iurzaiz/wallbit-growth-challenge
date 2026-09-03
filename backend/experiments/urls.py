from django.urls import path

from . import views

urlpatterns = [
    path("funding-screen", views.FundingScreenView.as_view(), name="funding-screen"),
]
