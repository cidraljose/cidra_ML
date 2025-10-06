"""Datasets page"""

import io
import json
import os
import uuid

import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import MergeDatasetsForm, SplitDatasetForm, UploadCSVForm
from .models import Dataset
from .plots import (
    create_correlation_heatmap,
    create_countplot,
    create_histogram,
    create_missing_values_plot,
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
        file=os.path.join("datasets", csv_filename),
        separator=",",
        encoding="utf-8",
        columns=columns_info,
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        uploaded_by=user if user and user.is_authenticated else None,
        description=description,
    )
    return new_dataset


@login_required
def manage_datasets(request):
    """
    Access and manage datasets.
    """

    if not os.path.exists(settings.DATASETS_DIR):
        os.makedirs(settings.DATASETS_DIR)

    # List datasets and handle upload form
    datasets = (
        Dataset.objects.filter(uploaded_by=request.user)
        .exclude(name="--manual-data--")
        .order_by("-date")
    )
    upload_form = UploadCSVForm()
    split_form = SplitDatasetForm(user=request.user)
    merge_form = MergeDatasetsForm(user=request.user)

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
                            "merge_form": merge_form,
                            "datasets": datasets,
                        },
                    )

                _create_dataset_instance(name, description, dataset, request.user)
                return redirect("manage_datasets_view")

        elif "split_dataset" in request.POST:
            # --- Handle Dataset Split ---
            split_form = SplitDatasetForm(request.POST, user=request.user)
            if split_form.is_valid():
                original_dataset = split_form.cleaned_data["dataset"]
                train_ratio = split_form.cleaned_data["train_split_ratio"] / 100.0

                original_file_path = original_dataset.file.path
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

        elif "merge_datasets" in request.POST:
            merge_form = MergeDatasetsForm(request.POST, user=request.user)
            if merge_form.is_valid():
                selected_datasets = merge_form.cleaned_data["datasets"]
                new_name = merge_form.cleaned_data["new_dataset_name"]

                if len(selected_datasets) < 2:
                    merge_form.add_error(
                        "datasets", "Please select at least two datasets to merge."
                    )
                else:
                    try:
                        dataframes_to_merge = []
                        for ds in selected_datasets:
                            # Get selected columns for this dataset from the POST data
                            selected_columns = request.POST.getlist(f"columns_{ds.id}")
                            if not selected_columns:
                                raise ValueError(
                                    f"No columns selected for dataset '{ds.name}'."
                                )

                            df = pd.read_csv(ds.file.path)
                            # Reset index to ensure alignment, drop old index
                            df = df[selected_columns].reset_index(drop=True)
                            dataframes_to_merge.append(df)

                        # Merge dataframes vertically
                        merged_df = pd.concat(
                            dataframes_to_merge, axis=0, ignore_index=True
                        )

                        # Create new dataset instance
                        _create_dataset_instance(
                            name=new_name,
                            description=f"Merged from {', '.join([d.name for d in selected_datasets])}",
                            df=merged_df,
                            user=request.user,
                        )
                        return redirect("manage_datasets_view")

                    except Exception as e:
                        merge_form.add_error(None, f"Error during merge: {e}")

    return render(
        request,
        "manage_datasets.html",
        {
            "upload_form": upload_form,
            "split_form": split_form,
            "merge_form": merge_form,
            "datasets": datasets,
        },
    )


@login_required
def delete_dataset(request, dataset_id):
    """
    Delete a dataset by its ID.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        if dataset.file:
            if os.path.exists(dataset.file.path):
                os.remove(dataset.file.path)
        dataset.delete()
    except Dataset.DoesNotExist:
        pass  # To implement

    return redirect("manage_datasets_view")


@login_required
def download_dataset(request, dataset_id):
    """
    Download a dataset by its ID.
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)

        if dataset.file:
            if os.path.exists(dataset.file.path):
                with open(dataset.file.path, "rb") as f:
                    response = HttpResponse(
                        f.read(), content_type="application/octet-stream"
                    )
                    response["Content-Disposition"] = (
                        f'attachment; filename="{os.path.basename(dataset.file.path)}"'
                    )
                    return response
    except Dataset.DoesNotExist:
        pass  # To implement

    return redirect("manage_datasets_view")


@login_required
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
        dataset_obj = Dataset.objects.get(pk=dataset_id, uploaded_by=request.user)
    except Dataset.DoesNotExist:
        return redirect("manage_datasets_view")

    refresh = request.GET.get("refresh", "false").lower() == "true"

    # Check if context is cached
    if (
        not refresh
        and dataset_obj.plots_context
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
        dataset_df = pd.read_csv(dataset_obj.file.path)

        # Stats
        stats = {}
        stats["description"] = dataset_df.describe().to_html(
            classes="table table-striped table-bordered"
        )
        buffer = io.StringIO()
        dataset_df.info(buf=buffer)
        stats["info"] = buffer.getvalue()
        stats["missing_values_plot"] = create_missing_values_plot(dataset_df)
        if not stats["missing_values_plot"]:
            stats["missing_values_message"] = "None of the features have empty values."
        else:
            stats["missing_values_message"] = None

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


@login_required
@require_POST
def get_multiple_dataset_columns(request):
    """
    Returns a JSON object with the columns for a list of dataset IDs.
    """
    try:
        data = json.loads(request.body)
        dataset_ids = data.get("dataset_ids", [])
        if not dataset_ids:
            return JsonResponse({"error": "No dataset IDs provided"}, status=400)

        datasets = Dataset.objects.filter(id__in=dataset_ids, uploaded_by=request.user)
        columns_data = {}
        for ds in datasets:
            columns_data[ds.id] = {
                "name": ds.name,
                "columns": (
                    list(ds.columns.keys()) if isinstance(ds.columns, dict) else []
                ),
            }

        return JsonResponse({"columns_data": columns_data})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({"error": str(e)}, status=400)
