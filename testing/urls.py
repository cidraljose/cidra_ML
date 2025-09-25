from django.urls import path

from manage_MLmodels.views import get_dataset_columns, get_model_details

from .views import testing

urlpatterns = [
    path("testing/", testing, name="testing_view"),
    path(
        "get-dataset-columns/<int:dataset_id>/",
        get_dataset_columns,
        name="get_dataset_columns_view",
    ),
    path(
        "get-model-details/<int:model_id>/",
        get_model_details,
        name="get_model_details_view",
    ),
]
