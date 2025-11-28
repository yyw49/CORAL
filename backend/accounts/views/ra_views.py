from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, date, timedelta
from accounts.models import LabAssistant
from accounts.permissions import IsScheduleAssistant


class LabAssistantSerializer(serializers.ModelSerializer):
    # 1. Basic Info
    name = serializers.CharField(source='user.get_full_name')
    email = serializers.EmailField(source='user.email')

    # 2. Availability (Badge Format)
    availability = serializers.SerializerMethodField()

    # 3. New Metric Fields (Renamed for clarity)
    totalCompletedHours = serializers.SerializerMethodField()
    dateRangeCompletedHours = serializers.SerializerMethodField()
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
            'dateRangeCompletedHours',  # Hours worked in requested range
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

    def _get_date_from_request(self, request, key):
        if not request:
            return None
        date_str = request.query_params.get(key)
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def get_dateRangeCompletedHours(self, obj):
        """
        RANGE HISTORY: Hours worked between start_date and end_date (inclusive).
        Defaults to the 1-week window starting from the most recent Monday.
        """
        request = self.context.get('request')
        start_date = self._get_date_from_request(request, 'start_date')
        end_date = self._get_date_from_request(request, 'end_date')

        # If only one bound is provided, infer a 7-day window
        if start_date and not end_date:
            end_date = start_date + timedelta(days=6)
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=6)

        today = timezone.now().date()

        # Default window: most recent Monday through Sunday
        if not start_date and not end_date:
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        # Safety fallback if a bound is still missing
        if not start_date:
            start_date = today - timedelta(days=today.weekday())
        if not end_date:
            end_date = start_date + timedelta(days=6)

        # Ensure chronological order
        if end_date < start_date:
            return 0

        assignments = obj.assignments.filter(
            study__date__range=[start_date, end_date],
            study__date__lte=today  # Only completed work
        ).select_related('study')

        total = 0
        for assign in assignments:
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

    @action(
        detail=False,
        methods=['get'],
        url_path='hours-worked',
        permission_classes=[IsScheduleAssistant]
    )
    def hours_worked(self, request):
        """
        GET /api/lab-assistants/hours-worked/?user_id=...&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
        Schedule admins can fetch hours worked for any RA in a given range.
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"detail": "user_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ra = LabAssistant.objects.select_related('user').get(user__id=user_id)
        except LabAssistant.DoesNotExist:
            return Response(
                {"detail": "Lab Assistant not found for provided user_id."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(ra)
        hours_worked = serializer.get_dateRangeCompletedHours(ra)

        return Response({
            "labAssistantId": ra.id,
            "labAssistantName": ra.user.get_full_name(),
            "dateRangeCompletedHours": hours_worked
        })
