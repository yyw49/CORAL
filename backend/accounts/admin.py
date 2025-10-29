from django.contrib import admin
from .models import LabAssistant, Day

@admin.register(LabAssistant)
class LabAssistantAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at']