"""Datasets page"""

import base64
import io
import os
import uuid

import matplotlib.pyplot as plt
import pandas as pd
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import UploadCSVForm
from .models import Dataset
from .utils import *


def manage_datasets(request):
    """
    Access and manage datasets.
    """

    # Assume settings.DATASETS_DIR is defined
    if not os.path.exists(settings.DATASETS_DIR):
        os.makedirs(settings.DATASETS_DIR)

    # List datasets and handle upload form
    datasets = Dataset.objects.all().order_by("-date")
    upload_form = UploadCSVForm()

    if request.method == "POST":
        if "upload_csv" in request.POST:
            upload_form = UploadCSVForm(request.POST, request.FILES)
            if upload_form.is_valid():
                # Extract form data
                file = upload_form.cleaned_data["file"]
                name = upload_form.cleaned_data["name"]
                encoding = upload_form.cleaned_data["encoding"]
                separator = upload_form.cleaned_data["separator"]
                description = upload_form.cleaned_data["description"]

                # Fix \t separator
                if separator == "\\t":
                    separator = "\t"

                # Read uploaded CSV file
                try:
                    dataset = pd.read_csv(file, sep=separator, encoding=encoding)
                except Exception as e:
                    upload_form.add_error("file", f"Erro ao ler o arquivo: {e}")
                    return render(
                        request,
                        "manage_datasets.html",
                        {"upload_form": upload_form, "datasets": datasets},
                    )

                # Standardize and save dataset
                # FIX: Save file with the same name that will be stored in the database
                csv_filename = f"{name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.csv"
                csv_path = os.path.join(settings.DATASETS_DIR, csv_filename)
                dataset.to_csv(csv_path, index=False, sep=",", encoding="utf-8")

                # Set columns info
                columns_info = {
                    col: str(dtype) for col, dtype in dataset.dtypes.items()
                }

                Dataset.objects.create(
                    name=name,
                    file=csv_filename,
                    separator=",",
                    encoding="utf-8",
                    columns=columns_info,
                    n_rows=dataset.shape[0],
                    n_columns=dataset.shape[1],
                    uploaded_by=request.user if request.user.is_authenticated else None,
                    description=description,
                )

                return redirect("manage_datasets_view")

    return render(
        request,
        "manage_datasets.html",
        {"upload_form": upload_form, "datasets": datasets},
    )


def delete_dataset(request, dataset_id):
    """
    Delete a dataset by its ID.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)

        if dataset.file:
            file_path = os.path.join(settings.DATASETS_DIR, dataset.file.name)
            if os.path.exists(file_path):
                os.remove(file_path)

        dataset.delete()
    except Dataset.DoesNotExist:
        pass  # Handle error - to implement

    return redirect("manage_datasets_view")


def download_dataset(request, dataset_id):
    """
    Download a dataset by its ID.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)

        if dataset.file:
            # FIX: Use the correct directory where datasets are stored
            file_path = os.path.join(settings.DATASETS_DIR, dataset.file.name)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    response = HttpResponse(
                        f.read(), content_type="application/octet-stream"
                    )
                    response["Content-Disposition"] = (
                        f'attachment; filename="{os.path.basename(file_path)}"'
                    )
                    return response
    except Dataset.DoesNotExist:
        pass  # Handle error - to implement

    return redirect("manage_datasets_view")


def visualize_dataset(request, dataset_id):  # Renamed from pk to dataset_id for clarity
    """
    Visualize a dataset by its ID.
    """

    # Assure dataset exists
    try:
        dataset_obj = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        return redirect("manage_datasets_view")  # Or render an error page

    file_path = os.path.join(settings.DATASETS_DIR, dataset_obj.file.name)
    dataset_df = pd.read_csv(
        file_path, sep=",", encoding="utf-8"  # Standardized on upload
    )

    # Generate stats
    stats = {}
    stats["description"] = dataset_df.describe().to_html(
        classes="table table-striped table-bordered"
    )
    buffer = io.StringIO()
    dataset_df.info(buf=buffer)
    stats["info"] = buffer.getvalue()

    # Generate plots for numerical columns
    plots = {}
    numerical_cols = dataset_df.select_dtypes(include=["number"]).columns.tolist()
    for col in numerical_cols:
        plots[f"hist_{col}"] = create_histogram(dataset_df, col)
        plots[f"box_{col}"] = create_boxplot(dataset_df, col)
    if len(numerical_cols) > 1:
        plots["correlation_heatmap"] = create_correlation_heatmap(
            dataset_df, numerical_cols
        )

    # Generate plots for categorical columns
    # Use 'object' as pandas often reads categorical data as object type from CSV
    categorical_cols = dataset_df.select_dtypes(include=["object"]).columns.tolist()
    for col in categorical_cols:
        plots[f"count_{col}"] = create_countplot(dataset_df, col)

    context = {
        "dataset": dataset_obj,
        "plots": plots,
        "stats": stats,
        "head": dataset_df.head().to_html(classes="table table-striped table-bordered"),
    }

    # Render the partial template, which will be fetched by the AJAX call
    return render(request, "_visualize_dataset_partial.html", context)
