from django.db import models
from django.contrib.auth.models import User


class LabAssistant(models.Model):
    class Role(models.TextChoices):
        RA = 'ra', 'Research Assistant'
        SCHEDULING_ADMIN = 'scheduling_admin', 'Scheduling Admin'
        FULL_ADMIN = 'full_admin', 'Full Admin'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # This replaces/augments is_schedule_assistant
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RA,
    )

    # you can keep this if you still want a separate flag,
    # but it's kind of redundant now
    is_schedule_assistant = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username



class SonaStudySchedule(models.Model):
    """
    Representation of a SONA study schedule entry that we can persist
    locally when needed.
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()  # when the study happens
    start_time = models.TimeField()  # when it starts
    end_time = models.TimeField()  # when it ends
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        LabAssistant,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_studies'
    )
    experiment_id = models.IntegerField(null=True, blank=True, db_index=True)
    timeslot_id = models.IntegerField(null=True, blank=True)
    timeslot_date = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    num_signed_up = models.IntegerField(null=True, blank=True)
    num_students = models.IntegerField(null=True, blank=True)
    researcher_id = models.IntegerField(null=True, blank=True)
    survey_flag = models.IntegerField(null=True, blank=True)
    web_flag = models.IntegerField(null=True, blank=True)
    videoconf_flag = models.IntegerField(null=True, blank=True)
    videoconf_url = models.URLField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time', 'name']

    def __str__(self):
        return f"{self.name} on {self.date} {self.start_time}-{self.end_time} @ {self.location}"


