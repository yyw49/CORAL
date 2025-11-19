from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.views import ra_views, auth, study_views

# 2. Setup the Router for your Data APIs
router = DefaultRouter()
router.register(r'studies', study_views.StudyViewSet, basename='study')
router.register(r'lab-assistants', ra_views.LabAssistantViewSet, basename='lab-assistant')

urlpatterns = [
    # --- 1. Developer Tools ---
    # Keeps the "Log In" button working in the browser interface


    path('login/', auth.login_view, name='api_login'),
    path('logout/', auth.logout_view, name='api_logout'),

    # --- 3. Data Endpoints ---
    # /studies/ and /lab-assistants/
    path('', include(router.urls)),

]