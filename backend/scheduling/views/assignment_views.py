from rest_framework import viewsets, serializers, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from scheduling.models import Assignment, Study, LabAssistant


# ==========================================
# 1. The Serializer
# ==========================================

class AssignmentSerializer(serializers.ModelSerializer):
    # Read-only fields for displaying helpful info in the list
    studyTitle = serializers.CharField(source='study.name', read_only=True)
    studyDate = serializers.DateField(source='study.date', read_only=True)
    studyStart = serializers.TimeField(source='study.start_time', read_only=True)
    studyEnd = serializers.TimeField(source='study.end_time', read_only=True)
    studyLocation = serializers.CharField(source='study.location', read_only=True)

    raName = serializers.CharField(source='lab_assistant.user.get_full_name', read_only=True)
    raEmail = serializers.CharField(source='lab_assistant.user.email', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id',
            'study',  # Input: ID of the study
            'lab_assistant',  # Input: ID of the RA
            'studyTitle',  # Output details...
            'studyDate',
            'studyStart',
            'studyEnd',
            'studyLocation',
            'raName',
            'raEmail',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        """
        Safety Check: Prevent Double Booking.
        Ensure the RA isn't already assigned to another study at the same time.
        """
        study = data.get('study')
        lab_assistant = data.get('lab_assistant')

        if not study or not lab_assistant:
            return data

        # 1. Get the time window of the target study
        target_date = study.date
        target_start = study.start_time
        target_end = study.end_time

        # 2. Find any EXISTING assignments for this RA on the same day
        conflicts = Assignment.objects.filter(
            lab_assistant=lab_assistant,
            study__date=target_date,
            # Check for time overlap: (StartA < EndB) and (EndA > StartB)
            study__start_time__lt=target_end,
            study__end_time__gt=target_start
        )

        # If this is an update to an existing assignment, exclude itself
        if self.instance:
            conflicts = conflicts.exclude(pk=self.instance.pk)

        if conflicts.exists():
            conflict_study = conflicts.first().study
            raise ValidationError(
                f"Conflict: {lab_assistant.user.get_full_name()} is already assigned to "
                f"'{conflict_study.name}' ({conflict_study.start_time}-{conflict_study.end_time}) on this date."
            )

        return data


# ==========================================
# 2. The ViewSet
# ==========================================

class AssignmentViewSet(viewsets.ModelViewSet):
    """
    API Endpoint: /api/assignments/
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Role-Based Access:
        - Admins: See ALL assignments.
        - RAs: See ONLY their own assignments.
        """
        user = self.request.user
        if not hasattr(user, 'labassistant'):
            return Assignment.objects.none()

        la = user.labassistant

        # Admin Check
        if la.role in ['full_admin', 'scheduling_admin']:
            # Allow filtering by Study ID or RA ID
            # Example: GET /api/assignments/?ra_id=5
            queryset = Assignment.objects.all().order_by('study__date', 'study__start_time')

            ra_id = self.request.query_params.get('ra_id')
            study_id = self.request.query_params.get('study_id')

            if ra_id:
                queryset = queryset.filter(lab_assistant_id=ra_id)
            if study_id:
                queryset = queryset.filter(study_id=study_id)

            return queryset

        # Regular RA: Only show my assignments
        return Assignment.objects.filter(lab_assistant=la).order_by('study__date', 'study__start_time')