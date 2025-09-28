"""manage_datasets URL Configuration"""

from django.urls import path

from .views import (
    delete_dataset,
    download_dataset,
    get_multiple_dataset_columns,
    manage_datasets,
    visualize_dataset,
)

urlpatterns = [
    path("manage_datasets/", manage_datasets, name="manage_datasets_view"),
    path(
        "manage_datasets/delete<int:dataset_id>/",
        delete_dataset,
        name="delete_dataset_view",
    ),
    path(
        "manage_datasets/download<int:dataset_id>/",
        download_dataset,
        name="download_dataset_view",
    ),
    path(
        "manage_datasets/visualize<int:dataset_id>/",
        visualize_dataset,
        name="visualize_dataset_view",
    ),
    path(
        "manage_datasets/merge/",
        get_multiple_dataset_columns,
        name="get_multiple_dataset_columns_view",
    ),
]
