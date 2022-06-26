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
        "<int:pk>/",
        views.RecordDetailView.as_view(),
        name="record_detail",
    ),
    path(
        "trxcredit_list/",
        views.TrxCreditListView.as_view(),
        name="trxcredit_list",
    ),
    path(
        "trxcredit_chart/",
        views.trxcredit_chart,
        name="trxcredit_chart",
    ),
    path(
        "search_TEMP/",
        views.search_TEMP,
        name="search_TEMP",
    ),
]
