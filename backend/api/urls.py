from django.urls import path

from api.views.sona_study_views import SonaStudyListView

urlpatterns = [
    path(
        "sona/studies/",
        SonaStudyListView.as_view(),
        name="sona-study-list",
    ),
]
