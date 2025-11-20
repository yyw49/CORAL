from rest_framework import serializers
from django.contrib.auth.models import User
from .models import LabAssistant, Availability, SonaStudySchedule, Assignment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class LabAssistantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LabAssistant
        fields = ['id', 'user', 'is_schedule_assistant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Availability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time']
        read_only_fields = ['id']

    def validate(self, data):
        """Ensure end_time is after start_time"""
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("end_time must be after start_time")
        return data


class StudySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.user.get_full_name',
        read_only=True
    )
    assigned_count = serializers.SerializerMethodField()

    class Meta:
        model = SonaStudySchedule
        fields = [
            'id', 'name', 'description', 'date', 'start_time', 'end_time',
            'created_by', 'created_by_name', 'assigned_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_assigned_count(self, obj):
        """Count how many assistants assigned to this study"""
        return obj.assignments.count()


class AssignmentSerializer(serializers.ModelSerializer):
    lab_assistant_name = serializers.CharField(
        source='lab_assistant.user.get_full_name',
        read_only=True
    )
    study_detail = StudySerializer(source='study', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id', 'lab_assistant', 'lab_assistant_name',
            'study', 'study_detail', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """Check for conflicts when creating assignment"""
        lab_assistant = data['lab_assistant']
        study = data['study']

        # Check if assistant is available on this day/time
        day_of_week = study.date.weekday()
        is_available = Availability.objects.filter(
            lab_assistant=lab_assistant,
            day_of_week=day_of_week,
            start_time__lte=study.start_time,
            end_time__gte=study.end_time
        ).exists()

        if not is_available:
            raise serializers.ValidationError(
                f"{lab_assistant.user.get_full_name()} is not available on "
                f"{study.get_day_of_week_display()} {study.start_time}-{study.end_time}"
            )

        # Check for scheduling conflicts (overlapping assignments)
        conflicts = Assignment.objects.filter(
            lab_assistant=lab_assistant,
            study__date=study.date,
            study__start_time__lt=study.end_time,
            study__end_time__gt=study.start_time
        ).exclude(study=study)

        if conflicts.exists():
            conflict = conflicts.first()
            raise serializers.ValidationError(
                f"{lab_assistant.user.get_full_name()} already has an assignment on "
                f"{study.date} during this time: {conflict.study.name}"
            )

        return data
