from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import LabAssistant, Availability
from accounts.serializers import LabAssistantSerializer, AvailabilitySerializer

class LabAssistantViewSet(viewsets.ModelViewSet):
    queryset = LabAssistant.objects.all()
    serializer_class = LabAssistantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get availability for a specific lab assistant"""
        lab_assistant = self.get_object()
        availabilities = lab_assistant.availabilities.all()
        serializer = AvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data)

class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter availability by lab_assistant if provided"""
        queryset = Availability.objects.all()
        lab_assistant_id = self.request.query_params.get('lab_assistant', None)
        if lab_assistant_id is not None:
            queryset = queryset.filter(lab_assistant_id=lab_assistant_id)
        return queryset