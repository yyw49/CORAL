from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, date, timedelta
from accounts.models import LabAssistant


class LabAssistantSerializer(serializers.ModelSerializer):
    # 1. Basic Info
    name = serializers.CharField(source='user.get_full_name')
    email = serializers.EmailField(source='user.email')

    # 2. Availability (Badge Format)
    availability = serializers.SerializerMethodField()

    # 3. New Metric Fields (Renamed for clarity)
    totalCompletedHours = serializers.SerializerMethodField()
    weeklyScheduledHours = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = LabAssistant
        fields = [
            'id',
            'name',
            'email',
            'availability',
            'totalCompletedHours',  # Replaces totalHours
            'weeklyScheduledHours',  # New field
            'avatar'
        ]

    def get_availability(self, obj):
        return [str(a) for a in obj.availabilities.all()]

    def _calculate_study_hours(self, study):
        """Helper to calculate duration of a single study in hours"""
        if study.start_time and study.end_time:
            dummy = date.today()
            start = datetime.combine(dummy, study.start_time)
            end = datetime.combine(dummy, study.end_time)
            return (end - start).total_seconds() / 3600
        return 0

    def get_totalCompletedHours(self, obj):
        """
        LIFETIME HISTORY: Sum of all assignments where the study date is in the past.
        """
        today = timezone.now().date()
        # Filter for strictly past assignments
        past_assignments = obj.assignments.filter(study__date__lt=today).select_related('study')

        total = 0
        for assign in past_assignments:
            total += self._calculate_study_hours(assign.study)
        return round(total, 1)

    def get_weeklyScheduledHours(self, obj):
        """
        CURRENT LOAD: Sum of ALL assignments (completed + pending) for THIS WEEK.
        Defined as Monday to Sunday of the current week.
        """
        today = timezone.now().date()

        # 1. Find the Monday of this week
        start_of_week = today - timedelta(days=today.weekday())

        # 2. Find the Sunday of this week
        end_of_week = start_of_week + timedelta(days=6)

        # 3. Filter assignments falling in this date range
        weekly_assignments = obj.assignments.filter(
            study__date__range=[start_of_week, end_of_week]
        ).select_related('study')

        total = 0
        for assign in weekly_assignments:
            total += self._calculate_study_hours(assign.study)
        return round(total, 1)

    def get_avatar(self, obj):
        return ""


class LabAssistantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-Only: List RAs for dropdowns and dashboard views.
    """
    queryset = LabAssistant.objects.all()
    serializer_class = LabAssistantSerializer

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        GET /api/lab-assistants/{id}/history/
        Returns a detailed list of past completed studies.
        """
        ra = self.get_object()
        today = timezone.now().date()

        history_assignments = ra.assignments.filter(
            study__date__lt=today
        ).select_related('study').order_by('-study__date')

        data = []
        for assignment in history_assignments:
            study = assignment.study

            # Calculate duration dynamically
            duration = 0
            if study.start_time and study.end_time:
                dummy = date.today()
                start = datetime.combine(dummy, study.start_time)
                end = datetime.combine(dummy, study.end_time)
                duration = (end - start).total_seconds() / 3600

            data.append({
                "studyId": study.id,
                "title": study.name,
                "date": study.date,
                "hours": round(duration, 1),
                "location": study.location,
                "status": "completed"
            })

        return Response(data)