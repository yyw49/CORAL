from django.db import models
from django.contrib.auth.models import User
from datetime import time, timedelta

class LabAssistant(models.Model):    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_assistant')
    is_schedule_assistant = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = 'Lab Assistant'
        verbose_name_plural = 'Lab Assistants'


class Schedule(models.Model):
    """
    Represents a schedule of assigned studies for a week.
    SchedulingAssistants will assign studies to LabAssistants for a given week.
    """

    monday = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='monday')
    tuesday = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='tuesday')
    wednesday = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='wednesday')
    thursday = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='thursday')
    friday = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='friday')

    DAYS = ['monday','tuesday','wednesday','thursday','friday']

class Availability(models.Model):
    """
    Represents a week's availability schedule containing 5 days (Monday-Friday).
    All LabAssistants can add their availability to the days in this object.
    """
    # store each weekday's slots in a JSONField: list of 32 slot dicts
    monday    = models.JSONField(default=Day._default_slots)
    tuesday   = models.JSONField(default=Day._default_slots)
    wednesday = models.JSONField(default=Day._default_slots)
    thursday  = models.JSONField(default=Day._default_slots)
    friday    = models.JSONField(default=Day._default_slots)

    DAYS = ['monday','tuesday','wednesday','thursday','friday']


class Day(models.Model):

    # 32 slots of 15 minutes each across 8 hours (9-5)
    SLOTS_PER_DAY = 32

    def _default_slots():
        # Each slot has:
        # 'assistants': list of LabAssistant IDs
        # 'scheduled_studies': mapping assistant ID -> Study ID (optional)
        return [{'assistants': [], 'scheduled_studies': {}} for _ in range(Day.SLOTS_PER_DAY)]
    slots = models.JSONField(default=_default_slots)

    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField()

class Study(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name