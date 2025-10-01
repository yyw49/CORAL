from django.db import models
from django.contrib.auth.models import User

class LabAssistant(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_assistant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = 'Lab Assistant'
        verbose_name_plural = 'Lab Assistants'


class Availability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    lab_assistant = models.ForeignKey(LabAssistant, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.lab_assistant.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    class Meta:
        ordering = ['lab_assistant', 'day_of_week', 'start_time']
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'