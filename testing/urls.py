from django.urls import path

from manage_MLmodels.views import get_dataset_columns, get_model_details

from .views import download_test_with_predictions, get_test_result_details, testing

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
        "results/<int:result_id>/details/",
        get_test_result_details,
        name="get_test_result_details_view",
    ),
    path(
        "results/<int:result_id>/download/",
        download_test_with_predictions,
        name="download_with_predictions_view",
    ),
]
