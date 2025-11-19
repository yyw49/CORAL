from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from studies import services
from studies.sona_client import SonaAPIError


class SonaStudyQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    include_raw = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError(
                {"end_date": "end_date must be greater than or equal to start_date."}
            )
        return attrs


class SonaStudyListView(APIView):
    """
    Return active SONA studies (lab only) for the requested time window.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query_serializer = SonaStudyQuerySerializer(
            data=request.query_params or None
        )
        query_serializer.is_valid(raise_exception=True)
        start = query_serializer.validated_data.get("start_date")
        end = query_serializer.validated_data.get("end_date")
        include_raw = query_serializer.validated_data.get("include_raw", False)

        try:
            studies = services.fetch_studies_for_window(
                start_date=start, end_date=end
            )
        except SonaAPIError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = [
            study.to_dict(include_raw=include_raw) for study in studies
        ]
        return Response({"count": len(payload), "results": payload})
