from django.db import models

from accounts.models import LabAssistant, Study

class Availability(models.Model):
    """Recurring weekly availability pattern"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    lab_assistant = models.ForeignKey(
        LabAssistant,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['lab_assistant', 'day_of_week', 'start_time']
        unique_together = [['lab_assistant', 'day_of_week', 'start_time']]

    def __str__(self):
        return f"{self.lab_assistant} {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class TimeEntry(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    lab_assistant = models.ForeignKey(
        LabAssistant,
        on_delete=models.CASCADE,
        related_name='time_entries' # This name is crucial for the queries below
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.SET_NULL,
        null=True,
        related_name='time_entries'
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=1) # Allows 4.5, 1.0, etc.
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lab_assistant} - {self.hours}h on {self.date}"

class Assignment(models.Model):
    """
    Which lab assistants are assigned to which study.
    A Study can have many lab assistants;
    a LabAssistant can be assigned to many Studies.
    """
    lab_assistant = models.ForeignKey(
        LabAssistant,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['study__date', 'study__start_time', 'lab_assistant']
        unique_together = [['lab_assistant', 'study']]

    def __str__(self):
        return f"{self.lab_assistant} assigned to {self.study}"