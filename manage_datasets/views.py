"""Datasets page"""

import io
import os
import uuid

import pandas as pd
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SplitDatasetForm, UploadCSVForm
from .models import Dataset
from .plots import (
    create_correlation_heatmap,
    create_countplot,
    create_histogram,
    create_normalized_pdf_plot,
)


def _create_dataset_instance(name, description, df, user):
    """Helper function to save a dataframe and create a Dataset model instance."""
    csv_filename = f"{name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.csv"
    csv_path = os.path.join(settings.DATASETS_DIR, csv_filename)
    df.to_csv(csv_path, index=False, sep=",", encoding="utf-8")

    columns_info = {col: str(dtype) for col, dtype in df.dtypes.items()}

    new_dataset = Dataset.objects.create(
        name=name,
        file=os.path.join("", csv_filename),
        separator=",",
        encoding="utf-8",
        columns=columns_info,
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        uploaded_by=user if user and user.is_authenticated else None,
        description=description,
    )
    return new_dataset


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
    split_form = SplitDatasetForm()

    if request.method == "POST":
        if "upload_csv" in request.POST:
            # --- Handle CSV Upload ---
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
                    upload_form.add_error("file", f"Error reading the file: {e}")
                    return render(
                        request,
                        "manage_datasets.html",
                        {
                            "upload_form": upload_form,
                            "split_form": split_form,
                            "datasets": datasets,
                        },
                    )

                _create_dataset_instance(name, description, dataset, request.user)
                return redirect("manage_datasets_view")

        elif "split_dataset" in request.POST:
            # --- Handle Dataset Split ---
            split_form = SplitDatasetForm(request.POST)
            if split_form.is_valid():
                original_dataset = split_form.cleaned_data["dataset"]
                train_ratio = split_form.cleaned_data["train_split_ratio"] / 100.0

                original_file_path = os.path.join(
                    settings.DATASETS_DIR, original_dataset.file.name
                )
                try:
                    original_df = pd.read_csv(original_file_path)

                    # Split the dataframe
                    train_df = original_df.sample(frac=train_ratio, random_state=42)
                    test_df = original_df.drop(train_df.index)

                    # Create train dataset
                    _create_dataset_instance(
                        name=f"{original_dataset.name}_train",
                        description=f"Training split from '{original_dataset.name}'",
                        df=train_df,
                        user=request.user,
                    )
                    # Create test dataset
                    _create_dataset_instance(
                        name=f"{original_dataset.name}_test",
                        description=f"Test split from '{original_dataset.name}'",
                        df=test_df,
                        user=request.user,
                    )
                    return redirect("manage_datasets_view")

                except Exception as e:
                    split_form.add_error(None, f"Error processing dataset: {e}")

    return render(
        request,
        "manage_datasets.html",
        {"upload_form": upload_form, "split_form": split_form, "datasets": datasets},
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
        pass  # To implement

    return redirect("manage_datasets_view")


def download_dataset(request, dataset_id):
    """
    Download a dataset by its ID.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)

        if dataset.file:
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
        pass  # To implement

    return redirect("manage_datasets_view")


def visualize_dataset(request, dataset_id):
    """
    Visualize a dataset by its ID.
    Saves generated plots and stats in the database for future access.

    Statistics:
        - Descriptive statistics
        - Info summary
    Plots for numerical columns:
        - PDF plots
        - Correlation heatmap
    Plots for categorical columns:
        - Count plots
    """
    # Assure dataset exists
    try:
        dataset_obj = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        return redirect("manage_datasets_view")

    # Check if context is cached
    if (
        dataset_obj.plots_context
        and dataset_obj.stats_context
        and dataset_obj.head_context
    ):
        context = {
            "dataset": dataset_obj,
            "plots": dataset_obj.plots_context,
            "stats": dataset_obj.stats_context,
            "head": dataset_obj.head_context,
        }
    else:  # generate, save, and then display
        file_path = os.path.join(settings.DATASETS_DIR, dataset_obj.file.name)
        dataset_df = pd.read_csv(file_path)

        # Stats
        stats = {}
        stats["description"] = dataset_df.describe().to_html(
            classes="table table-striped table-bordered"
        )
        buffer = io.StringIO()
        dataset_df.info(buf=buffer)
        stats["info"] = buffer.getvalue()

        # Numerial columns plots
        plots = {}
        numerical_cols = dataset_df.select_dtypes(include=["number"]).columns.tolist()
        if numerical_cols:
            plots["pdf_plot"] = create_normalized_pdf_plot(dataset_df, numerical_cols)
            plots["correlation_heatmap"] = create_correlation_heatmap(
                dataset_df, numerical_cols
            )
            for col in numerical_cols:
                plots[f"histo_{col}"] = create_histogram(dataset_df, col)

        # Categorical columns plots
        categorical_cols = dataset_df.select_dtypes(include=["object"]).columns.tolist()
        for col in categorical_cols:
            plots[f"count_{col}"] = create_countplot(dataset_df, col)

        # Save context
        dataset_obj.plots_context = plots
        dataset_obj.stats_context = stats
        dataset_obj.head_context = dataset_df.head().to_html(
            classes="table table-striped table-bordered"
        )
        dataset_obj.save()

        context = {
            "dataset": dataset_obj,
            "plots": plots,
            "stats": stats,
            "head": dataset_obj.head_context,
        }

    return render(request, "_visualize_dataset_partial.html", context)
