from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from accounts.models import LabAssistant, Availability
from accounts.serializers import LabAssistantSerializer, AvailabilitySerializer


class LabAssistantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lab Assistants
    """
    queryset = LabAssistant.objects.all()
    serializer_class = LabAssistantSerializer
    permission_classes = [AllowAny]  # For demo - remove in production!

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get availability for a specific lab assistant
        """
        lab_assistant = self.get_object()
        availability = Availability.objects.filter(lab_assistant=lab_assistant)
        serializer = AvailabilitySerializer(availability, many=True)
        return Response(serializer.data)


class AvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Availability records
    """
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [AllowAny]  # For demo - remove in production!

    def get_queryset(self):
        """
        Optionally filter availability by lab_assistant query parameter
        """
        queryset = Availability.objects.all()
        lab_assistant_id = self.request.query_params.get('lab_assistant', None)
        
        if lab_assistant_id is not None:
            queryset = queryset.filter(lab_assistant_id=lab_assistant_id)
        
        return queryset