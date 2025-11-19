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



class Study(models.Model):
    """
    A single scheduled study session (one concrete event).
    The admin fills: name, description, date, start_time, end_time.
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time', 'name']

    def __str__(self):
        return f"{self.name} on {self.date} {self.start_time}-{self.end_time} @ {self.location}"



