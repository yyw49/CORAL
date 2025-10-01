from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabAssistantViewSet, AvailabilityViewSet

router = DefaultRouter()
router.register(r'lab-assistants', LabAssistantViewSet, basename='labassistant')
router.register(r'availability', AvailabilityViewSet, basename='availability')

urlpatterns = [
    path('', include(router.urls)),
]