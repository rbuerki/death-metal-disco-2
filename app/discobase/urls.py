from django.urls import path
from discobase import views

app_name = "discobase"

urlpatterns = [
    path("list_record/", views.RecordListView.as_view(), name="list_record"),
]
