from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

class LabAssistant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_assistant')
    is_schedule_assistant = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name()


class AvailabilityDay(models.Model):
    SLOTS_PER_DAY = 32
    slots = models.JSONField(default=lambda: {i: 0 for i in range(SLOTS_PER_DAY)})  # 0=unavailable, 1=available
    date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Availability(models.Model):
    lab_assistant = models.OneToOneField(LabAssistant, on_delete=models.CASCADE, related_name='availability')

    monday    = models.OneToOneField(AvailabilityDay, on_delete=models.CASCADE, related_name='+')
    tuesday   = models.OneToOneField(AvailabilityDay, on_delete=models.CASCADE, related_name='+')
    wednesday = models.OneToOneField(AvailabilityDay, on_delete=models.CASCADE, related_name='+')
    thursday  = models.OneToOneField(AvailabilityDay, on_delete=models.CASCADE, related_name='+')
    friday    = models.OneToOneField(AvailabilityDay, on_delete=models.CASCADE, related_name='+')

    DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    def get_day(self, day_index: int) -> AvailabilityDay:
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0-4")
        return getattr(self, self.DAYS[day_index])


class ScheduleDay(models.Model):
    SLOTS_PER_DAY = 32
    slots = models.JSONField(default=lambda: {i: -1 for i in range(SLOTS_PER_DAY)})  # -1 = empty, else study_id
    date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Schedule(models.Model):
    lab_assistant = models.ForeignKey(LabAssistant, on_delete=models.CASCADE, related_name='schedules')
    start_date = models.DateField()  # first day of the week (Monday)


    monday    = models.OneToOneField(ScheduleDay, on_delete=models.CASCADE, related_name='+')
    tuesday   = models.OneToOneField(ScheduleDay, on_delete=models.CASCADE, related_name='+')
    wednesday = models.OneToOneField(ScheduleDay, on_delete=models.CASCADE, related_name='+')
    thursday  = models.OneToOneField(ScheduleDay, on_delete=models.CASCADE, related_name='+')
    friday    = models.OneToOneField(ScheduleDay, on_delete=models.CASCADE, related_name='+')

    DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    def get_day(self, day_index: int) -> ScheduleDay:
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0-4")
        return getattr(self, self.DAYS[day_index])


class Study(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
