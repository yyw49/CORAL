from django.contrib import admin
from .models import LabAssistant, Availability

@admin.register(LabAssistant)
class LabAssistantAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['lab_assistant', 'day_of_week', 'start_time', 'end_time']
    list_filter = ['day_of_week']
    search_fields = ['lab_assistant__user__first_name', 'lab_assistant__user__last_name']