from django.urls import path

from manage_MLmodels.views import get_dataset_columns

from .views import testing

urlpatterns = [
    path("testing/", testing, name="testing_view"),
    path(
        "get-dataset-columns/<int:dataset_id>/",
        get_dataset_columns,
        name="get_dataset_columns_view",
    ),
]
