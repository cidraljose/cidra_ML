"""manage_models URL Configuration"""

from django.urls import path

from .views import (
    delete_MLmodel,
    download_MLmodel,
    get_dataset_columns,
    get_MLmodel_row_partial,
    manage_MLmodels,
    visualize_MLmodel,
)

urlpatterns = [
    path("manage_MLmodels/", manage_MLmodels, name="manage_MLmodels_view"),
    path(
        "manage_MLmodels/delete/<int:MLmodel_id>/",
        delete_MLmodel,
        name="delete_MLmodel_view",
    ),
    path(
        "manage_MLmodels/download/<int:MLmodel_id>/",
        download_MLmodel,
        name="download_MLmodel_view",
    ),
    path(
        "manage_MLmodels/visualize/<int:MLmodel_id>/",
        visualize_MLmodel,
        name="visualize_MLmodel_view",
    ),
    path(
        "manage_MLmodels/get_dataset_columns/<int:dataset_id>/",
        get_dataset_columns,
        name="get_model_dataset_columns_view",
    ),
    path(
        "manage_MLmodels/<int:MLmodel_id>/row/",
        get_MLmodel_row_partial,
        name="get_MLmodel_row_partial",
    ),
]
