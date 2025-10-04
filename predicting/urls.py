from django.urls import path

from .views import delete_prediction_result, download_prediction_file, predicting

urlpatterns = [
    path("predicting/", predicting, name="predicting_view"),
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
]
