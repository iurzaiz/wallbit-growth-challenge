from django.db.models import Q
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .results import compute_variant_results
from .serializers import (
    DepositWebhookSerializer,
    FundingScreenSerializer,
    TrackEventSerializer,
    UserSerializer,
    VariantResultSerializer,
)


class FundingScreenView(APIView):
    def get(self, request):
        serializer = FundingScreenSerializer(data={"user_id": request.query_params.get("user_id")})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DepositWebhookView(APIView):
    def post(self, request):
        serializer = DepositWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrackEventView(APIView):
    def post(self, request):
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExperimentResultsView(APIView):
    def get(self, request):
        serializer = VariantResultSerializer(compute_variant_results(), many=True)
        return Response(serializer.data)


class UserPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class UserListView(generics.ListAPIView):
    """Lets whoever is testing this pick a real user_id without having to
    open data/users.json by hand. Paginated + filterable by ?q= (id or
    country) so the frontend never has to load all 1200 at once."""

    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_queryset(self):
        queryset = User.objects.order_by("country", "id")
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(Q(id__icontains=q) | Q(country__icontains=q))
        return queryset
