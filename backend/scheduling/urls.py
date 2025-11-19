from django.urls import path, include
from rest_framework.routers import DefaultRouter
from scheduling.views.time_entry_views import TimeEntryViewSet
from scheduling.views.availability_views import AvailabilityViewSet
from scheduling.views.assignment_views import AssignmentViewSet

# Create a router specific to the Scheduling App
router = DefaultRouter()
router.register(r'hours', TimeEntryViewSet, basename='time-entry')
router.register(r'availabilities', AvailabilityViewSet, basename='availability')
router.register(r'assignments', AssignmentViewSet, basename='assignment')

urlpatterns = [
    # This includes: GET /hours/, POST /hours/, etc.
    path('', include(router.urls)),
]