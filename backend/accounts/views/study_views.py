from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, date

# Import your existing models
from accounts.models import Study, LabAssistant
from scheduling.models import Assignment
from studies import services as sona_services
from studies.sona_client import SonaAPIError


# ==========================================
# 1. The Serializer
# ==========================================

class StudySerializer(serializers.ModelSerializer):
    # --- INPUT MAPPING (Frontend -> Backend) ---
    # Frontend sends "title", Model stores "name"
    title = serializers.CharField(source='name')

    # Frontend sends "time", Model stores "start_time"
    time = serializers.TimeField(source='start_time', format='%H:%M')

    # Frontend sends "endTime", Model stores "end_time"
    # We map this directly now, so no math is needed on save
    endTime = serializers.TimeField(source='end_time', format='%H:%M')

    # --- OUTPUT MAPPING (Backend -> Frontend) ---
    # We still calculate duration for the DISPLAY (e.g. "2.5 hours")
    # But we don't use it for input anymore.
    duration = serializers.SerializerMethodField()
    assignedRA = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Study
        fields = [
            'id',
            'title',       # Maps to name
            'description',
            'date',
            'time',        # Maps to start_time
            'endTime',     # Maps to end_time
            'location',
            'duration',    # Calculated Output (Read-only)
            'assignedRA',  # Calculated Output (Read-only)
            'status'       # Calculated Output (Read-only)
        ]
        read_only_fields = ['id', 'assignedRA', 'status', 'duration']

    def create(self, validated_data):
        """
        Simplified Create: No math needed.
        We just need to attach the 'created_by' user.
        """
        # Handle the 'created_by' field if your context has the user
        request = self.context.get('request')
        if request and hasattr(request.user, 'labassistant'):
            validated_data['created_by'] = request.user.labassistant

        return super().create(validated_data)

    def get_duration(self, obj):
        """
        Calculates duration for the frontend to display.
        Example: 14:00 to 15:30 -> Returns 1.5
        """
        if obj.start_time and obj.end_time:
            dummy_date = date.today()
            start = datetime.combine(dummy_date, obj.start_time)
            end = datetime.combine(dummy_date, obj.end_time)
            diff = end - start
            return diff.total_seconds() / 3600
        return 0

    def get_status(self, obj):
        """Logic for 'open', 'assigned', or 'completed'"""
        # 1. Check if completed (past date/time)
        if obj.date and obj.end_time:
            # Make timezone aware in production if needed
            study_end_dt = datetime.combine(obj.date, obj.end_time)
            if study_end_dt < datetime.now():
                return 'completed'

        # 2. Check if assigned
        if obj.assignments.exists():
            return 'assigned'

        # 3. Default
        return 'open'

    def get_assignedRA(self, obj):
        """Returns the name of the RA if one is assigned"""
        assignment = obj.assignments.first()
        if assignment:
            return assignment.lab_assistant.user.get_full_name() or assignment.lab_assistant.user.username
        return None


class SonaScheduleRequestSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError(
                {"end_date": "end_date must be greater than or equal to start_date."}
            )
        return attrs


# ==========================================
# 2. The ViewSet
# ==========================================

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.all().order_by('-date', '-start_time')
    serializer_class = StudySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """ POST /api/studies/{id}/assign/ """
        study = self.get_object()
        ra_name = request.data.get('ra_name')

        if not ra_name:
            return Response({"error": "ra_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fuzzy search for RA by name
        first_name = ra_name.split(' ')[0]
        ra = LabAssistant.objects.filter(user__first_name__icontains=first_name).first()

        if not ra:
            return Response({"error": "Research Assistant not found"}, status=status.HTTP_404_NOT_FOUND)

        # Assign
        Assignment.objects.create(study=study, lab_assistant=ra)

        return Response({
            "status": "assigned",
            "assignedRA": ra.user.get_full_name(),
            "message": f"Assigned to {ra.user.get_full_name()}"
        })

    @action(detail=True, methods=['post'])
    def unassign(self, request, pk=None):
        """ POST /api/studies/{id}/unassign/ """
        study = self.get_object()
        study.assignments.all().delete()
        return Response({
            "status": "open",
            "assignedRA": None,
            "message": "Unassigned successfully"
        })

    @action(detail=True, methods=['post'])
    def auto_assign(self, request, pk=None):
        """ POST /api/studies/{id}/auto_assign/ """
        study = self.get_object()
        ras = LabAssistant.objects.all()
        selected_ra = None

        # Basic Greedy Algorithm: Find first non-conflicting RA
        for ra in ras:
            is_busy = Assignment.objects.filter(
                lab_assistant=ra,
                study__date=study.date,
                study__start_time__lt=study.end_time,
                study__end_time__gt=study.start_time
            ).exists()

            if not is_busy:
                selected_ra = ra
                break

        if selected_ra:
            Assignment.objects.create(study=study, lab_assistant=selected_ra)
            return Response({
                "success": True,
                "assignedRA": selected_ra.user.get_full_name(),
                "message": f"Auto-assigned to {selected_ra.user.get_full_name()}"
            })
        else:
            return Response({
                "success": False,
                "message": "No available RA found."
            }, status=status.HTTP_409_CONFLICT)

    @action(detail=False, methods=['get'], url_path='sona-schedules')
    def sona_schedules(self, request):
        """ GET /api/studies/sona-schedules/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD """
        serializer = SonaScheduleRequestSerializer(
            data=request.query_params or None
        )
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data['start_date']
        end = serializer.validated_data['end_date']

        try:
            schedules = sona_services.fetch_studies_for_window(
                start_date=start,
                end_date=end,
            )
        except SonaAPIError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            "count": len(schedules),
            "results": [schedule.to_dict() for schedule in schedules],
        })
