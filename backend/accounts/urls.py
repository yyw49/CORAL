from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.views import ra_views, auth, study_views

# Setup the Router for your Data APIs
router = DefaultRouter()
router.register(r'studies', study_views.StudyViewSet, basename='study')
router.register(r'lab-assistants', ra_views.LabAssistantViewSet, basename='lab-assistant')

urlpatterns = [
    # --- Authentication Endpoints ---
    path('register/', auth.register, name='register'),
    path('login/', auth.login_view, name='api_login'),
    path('logout/', auth.logout_view, name='api_logout'),
    path('me/', auth.me, name='current_user'),

    # --- Data Endpoints ---
    # /studies/ and /lab-assistants/
    path('', include(router.urls)),
]