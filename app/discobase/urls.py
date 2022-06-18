from django.urls import path
from discobase import views

app_name = "discobase"

urlpatterns = [
    path(
        "record_list/",
        views.RecordListView.as_view(),
        name="record_list",
    ),
    path(
        "trxcredit_list/",
        views.TrxCreditListView.as_view(),
        name="trxcredit_list",
    ),
    path(
        "<int:pk>/",
        views.RecordDetailView.as_view(),
        name="record_detail",
    ),
]
