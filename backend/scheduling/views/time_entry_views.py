from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from scheduling.models import TimeEntry
from accounts.models import Study


# ==========================================
# 1. The Serializer
# ==========================================

class TimeEntrySerializer(serializers.ModelSerializer):
    # Read-Only fields for Displaying info to the Frontend
    raName = serializers.CharField(source='lab_assistant.user.get_full_name', read_only=True)
    studyTitle = serializers.CharField(source='study.name', read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            'id',
            'raName',  # For Admin display
            'study',  # Input: ID of the study
            'studyTitle',  # Output: Name of the study
            'date',
            'hours',
            'status',
            'notes'
        ]
        read_only_fields = ['id', 'raName', 'studyTitle']

    def validate_status(self, value):
        """
        Prevent RAs from setting their own status to 'approved' directly
        during creation/update (Security).
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'labassistant'):
            la = request.user.labassistant
            # If regular RA tries to set Approved, force it to Pending
            if la.role == 'ra' and value == TimeEntry.Status.APPROVED:
                return TimeEntry.Status.PENDING
        return value


# ==========================================
# 2. The ViewSet
# ==========================================

class TimeEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Role-Based Access Control:
        - Admins: See ALL time entries (for approval).
        - RAs: See ONLY their own time entries.
        """
        user = self.request.user
        if not hasattr(user, 'labassistant'):
            return TimeEntry.objects.none()

        la = user.labassistant

        # Check if Admin (Strings matching your LabAssistant.Role choices)
        if la.role in ['full_admin', 'scheduling_admin']:
            return TimeEntry.objects.all().order_by('-date', '-created_at')

        # Default: Regular RA
        return TimeEntry.objects.filter(lab_assistant=la).order_by('-date', '-created_at')

    def perform_create(self, serializer):
        """
        Auto-assign the logged-in LabAssistant as the owner of this entry.
        """
        user = self.request.user
        if not hasattr(user, 'labassistant'):
            raise ValidationError("User is not a Lab Assistant")

        # Force status to PENDING on create (unless overridden by logic)
        serializer.save(
            lab_assistant=user.labassistant,
            status=TimeEntry.Status.PENDING
        )

    # --- Admin Actions ---

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        POST /api/hours/{id}/approve/
        """
        entry = self.get_object()
        self._check_admin_permissions(request)

        entry.status = TimeEntry.Status.APPROVED
        entry.save()
        return Response({'status': 'approved', 'message': 'Hours approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        POST /api/hours/{id}/reject/
        """
        entry = self.get_object()
        self._check_admin_permissions(request)

        entry.status = TimeEntry.Status.REJECTED
        entry.save()
        return Response({'status': 'rejected', 'message': 'Hours rejected'})

    def _check_admin_permissions(self, request):
        """Helper to ensure only admins call approve/reject"""
        user = request.user
        if not hasattr(user, 'labassistant') or user.labassistant.role == 'ra':
            raise PermissionDenied("Only admins can approve or reject hours.")