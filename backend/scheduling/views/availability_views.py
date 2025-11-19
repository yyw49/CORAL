from rest_framework import viewsets, serializers, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from scheduling.models import Availability, LabAssistant


# ==========================================
# 1. The Serializer
# ==========================================

class AvailabilitySerializer(serializers.ModelSerializer):
    # --- INPUT/OUTPUT MAPPING ---
    # Frontend sends/receives 'day', Model stores 'day_of_week'
    day = serializers.ChoiceField(source='day_of_week', choices=Availability.DAY_CHOICES)

    # Frontend sends/receives 'startTime', Model stores 'start_time'
    startTime = serializers.TimeField(source='start_time', format='%H:%M')

    # Frontend sends/receives 'endTime', Model stores 'end_time'
    endTime = serializers.TimeField(source='end_time', format='%H:%M')

    # Read-only fields for Admin UI to identify the user
    labAssistantName = serializers.CharField(source='lab_assistant.user.get_full_name', read_only=True)
    labAssistantId = serializers.IntegerField(source='lab_assistant.id', read_only=True)

    class Meta:
        model = Availability
        fields = ['id', 'day', 'startTime', 'endTime', 'labAssistantName', 'labAssistantId']
        read_only_fields = ['id', 'labAssistantName', 'labAssistantId']

    def validate(self, data):
        """
        Validate that start < end and check for overlapping slots.
        """
        user = self.context['request'].user
        if not hasattr(user, 'labassistant'):
            raise ValidationError("User is not a Lab Assistant")

        # Determine which RA we are validating for.
        # If creating, it's the logged-in user (handled in perform_create).
        # If updating, we check the instance's owner.
        if self.instance:
            lab_assistant = self.instance.lab_assistant
        else:
            lab_assistant = user.labassistant

        day = data.get('day_of_week')
        start = data.get('start_time')
        end = data.get('end_time')

        # 1. Basic Logic Check
        if start and end and start >= end:
            raise ValidationError({"endTime": "End time must be after start time."})

        # 2. Overlap Check
        # We look for any slot for this RA, on this Day, where time overlaps.
        overlaps = Availability.objects.filter(
            lab_assistant=lab_assistant,
            day_of_week=day,
            start_time__lt=end,
            end_time__gt=start
        )

        # If this is an update, exclude the current slot itself from the check
        if self.instance:
            overlaps = overlaps.exclude(pk=self.instance.pk)

        if overlaps.exists():
            raise ValidationError("This time slot overlaps with an existing availability.")

        return data


# ==========================================
# 2. The ViewSet
# ==========================================

class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Role-Based Access:
        - Admins: Can see ALL availability (and filter by ?ra_id=X).
        - RAs: Can ONLY see their own availability.
        """
        user = self.request.user
        if not hasattr(user, 'labassistant'):
            return Availability.objects.none()

        la = user.labassistant

        # Check if Admin (assuming role names from your LabAssistant model)
        if la.role in ['full_admin', 'scheduling_admin']:
            queryset = Availability.objects.all().order_by('lab_assistant', 'day_of_week', 'start_time')

            # Optional Filter: GET /api/availabilities/?ra_id=5
            target_ra_id = self.request.query_params.get('ra_id')
            if target_ra_id:
                queryset = queryset.filter(lab_assistant_id=target_ra_id)

            return queryset

        # Default: Regular RA sees only their own
        return Availability.objects.filter(lab_assistant=la).order_by('day_of_week', 'start_time')

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in LabAssistant to the new slot.
        """
        user = self.request.user
        if not hasattr(user, 'labassistant'):
            raise ValidationError("You must be a Lab Assistant to set availability.")

        serializer.save(lab_assistant=user.labassistant)