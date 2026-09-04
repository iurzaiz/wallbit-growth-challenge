from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .results import compute_variant_results
from .serializers import DepositWebhookSerializer, FundingScreenSerializer, VariantResultSerializer


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


class ExperimentResultsView(APIView):
    def get(self, request):
        serializer = VariantResultSerializer(compute_variant_results(), many=True)
        return Response(serializer.data)
