from rest_framework import serializers
from django.contrib.auth.models import User
from .models import LabAssistant, Availability

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']

class LabAssistantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LabAssistant
        fields = ['id', 'user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AvailabilitySerializer(serializers.ModelSerializer):
    lab_assistant_name = serializers.CharField(source='lab_assistant.user.get_full_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Availability
        fields = ['id', 'lab_assistant', 'lab_assistant_name', 'day_of_week', 'day_name', 'start_time', 'end_time']
        read_only_fields = ['id', 'lab_assistant_name', 'day_name']