from django.urls import path

from .views import (
    delete_prediction_result,
    download_prediction_file,
    get_model_features,
    get_prediction_result_row_partial,
    predicting,
    visualize_prediction,
)

urlpatterns = [
    path("predicting/", predicting, name="predicting_view"),
    path(
        "predicting/get-model-features/<int:model_id>/",
        get_model_features,
        name="get_model_features",
    ),
    path(
        "predicting/visualize/<int:result_id>/",
        visualize_prediction,
        name="visualize_prediction_view",
    ),
    path(
        "predicting/download/<int:result_id>/",
        download_prediction_file,
        name="download_prediction_view",
    ),
    path(
        "predicting/delete/<int:result_id>/",
        delete_prediction_result,
        name="delete_prediction_view",
    ),
    path(
        "predicting/results/<int:result_id>/row/",
        get_prediction_result_row_partial,
        name="get_prediction_result_row_partial_view",
    ),
]
