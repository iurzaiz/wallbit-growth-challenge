from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FundingScreenSerializer


class FundingScreenView(APIView):
    def get(self, request):
        serializer = FundingScreenSerializer(data={"user_id": request.query_params.get("user_id")})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
