from django.urls import path

from manage_MLmodels.views import get_dataset_columns, get_model_details

from .views import (
    delete_test_result,
    download_test_with_predictions,
    get_test_result_details,
    get_test_result_row_partial,
    testing,
)

urlpatterns = [
    path("testing/", testing, name="testing_view"),
    path(
        "datasets/<int:dataset_id>/columns/",
        get_dataset_columns,
        name="get_dataset_columns_view",
    ),
    path(
        "models/<int:model_id>/details/",
        get_model_details,
        name="get_model_details_view",
    ),
    path(
        "testing/results/<int:result_id>/details/",
        get_test_result_details,
        name="get_test_result_details_view",
    ),
    path(
        "testing/results/<int:result_id>/download/",
        download_test_with_predictions,
        name="download_with_predictions_view",
    ),
    path(
        "testing/results/<int:result_id>/delete/",
        delete_test_result,
        name="delete_test_result_view",
    ),
    path(
        "testing/results/<int:result_id>/row/",
        get_test_result_row_partial,
        name="get_test_result_row_partial_view",
    ),
]
