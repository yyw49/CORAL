from django.contrib import admin
from .models import LabAssistant, Study
from scheduling.models import Availability, Assignment


@admin.register(LabAssistant)
class LabAssistantAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_schedule_assistant', 'created_at', 'updated_at']
    list_filter = ['is_schedule_assistant']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['lab_assistant', 'day_of_week_display', 'start_time', 'end_time']
    list_filter = ['day_of_week']
    search_fields = [
        'lab_assistant__user__first_name',
        'lab_assistant__user__last_name',
        'lab_assistant__user__email',
    ]

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = "Day of week"


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'start_time', 'end_time', 'location', 'created_by', 'created_at']
    list_filter = ['date', 'location']
    search_fields = ['name', 'location', 'description']
    date_hierarchy = 'date'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['lab_assistant', 'study', 'study_date', 'created_at']
    list_filter = ['study__date']
    search_fields = [
        'lab_assistant__user__first_name',
        'lab_assistant__user__last_name',
        'study__name',
    ]

    def study_date(self, obj):
        return obj.study.date
    study_date.admin_order_field = 'study__date'
    study_date.short_description = "Study date"
