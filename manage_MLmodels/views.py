import json
import os
import shutil
import tempfile
import zipfile

import pandas as pd
from autogluon.tabular import TabularPredictor
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from manage_datasets.models import Dataset
from testing.models import TestResult

from .forms import TrainMLModelForm, UploadMLModelForm
from .models import MLModel
from .tasks import train_autogluon_model


@login_required
@require_GET
def get_dataset_columns(request, dataset_id):
    """
    Returns JSON with dataset columns (list of strings).
    Handles different formats of dataset.columns (dict, list, etc.).
    """
    try:
        # Ensure user can only access their own datasets
        dataset = Dataset.objects.get(pk=dataset_id, uploaded_by=request.user)
    except Dataset.DoesNotExist:
        return JsonResponse({"columns": [], "error": "Dataset not found"}, status=404)

    cols_field = getattr(dataset, "columns", None)
    columns = []
    if isinstance(cols_field, dict):
        columns = list(cols_field.keys())
    elif isinstance(cols_field, (list, tuple)):
        columns = list(cols_field)
    else:
        # Generic attempt (e.g., JSONField with keys())
        try:
            columns = list(cols_field.keys())
        except Exception:
            try:
                columns = list(cols_field)
            except Exception:
                columns = []

    return JsonResponse({"columns": columns})


@login_required
def manage_MLmodels(request):
    upload_form = None
    train_form = None
    selected_target = ""
    selected_features = []

    # POST handling
    if request.method == "POST":
        # Upload
        if "upload_model" in request.POST:
            upload_form = UploadMLModelForm(
                request.POST,
                request.FILES,
                prefix="upload",
                user=request.user,
            )
            if upload_form.is_valid():
                uploaded_file = upload_form.cleaned_data["file"]
                model_name = upload_form.cleaned_data["name"]

                # Handle zipped AutoGluon model directories
                if uploaded_file.name.endswith(".zip"):
                    model_storage_path = os.path.join("MLmodels", model_name)
                    final_model_dir = os.path.join(
                        settings.MEDIA_ROOT, model_storage_path
                    )

                    if os.path.exists(final_model_dir):
                        upload_form.add_error(
                            "name",
                            "A model directory with this name already exists. Please choose a different name.",
                        )
                    else:
                        with tempfile.TemporaryDirectory() as tmpdir:
                            try:
                                with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                                    zip_ref.extractall(tmpdir)

                                # Check for a single root folder inside the zip
                                extracted_items = os.listdir(tmpdir)
                                source_dir = tmpdir
                                if len(extracted_items) == 1 and os.path.isdir(
                                    os.path.join(tmpdir, extracted_items[0])
                                ):
                                    source_dir = os.path.join(
                                        tmpdir, extracted_items[0]
                                    )

                                # Attempt to auto-fill features
                                auto_features = []
                                try:
                                    temp_predictor = TabularPredictor.load(source_dir)
                                    auto_features = temp_predictor.features()
                                except Exception:
                                    pass  # Ignore if predictor can't be loaded

                                # Use form features if provided, otherwise use auto-detected
                                form_features_raw = upload_form.cleaned_data.get(
                                    "features"
                                )
                                if form_features_raw:
                                    features_list = [
                                        f.strip() for f in form_features_raw.split(",")
                                    ]
                                else:
                                    features_list = auto_features

                                # Copy the contents to the final destination
                                shutil.copytree(source_dir, final_model_dir)

                                MLModel.objects.create(
                                    name=model_name,
                                    description=upload_form.cleaned_data["description"],
                                    target=upload_form.cleaned_data["target"],
                                    features=features_list,
                                    file=model_storage_path,
                                    related_dataset=upload_form.cleaned_data[
                                        "related_dataset"
                                    ],
                                    uploaded_by=request.user,
                                    status="COMPLETED",
                                )
                            except Exception as e:
                                upload_form.add_error(
                                    "file", f"Failed to process zip file: {e}"
                                )
                else:
                    # Handle non-zip files (or show an error if only zips are allowed)
                    upload_form.add_error(
                        "file", "Invalid file type. Only .zip archives are allowed."
                    )

            # If form is still valid (no errors added), redirect
            if upload_form.is_valid():
                return redirect("manage_MLmodels_view")

        # Train
        elif "train_model" in request.POST:
            train_form = TrainMLModelForm(
                request.POST, prefix="train", user=request.user
            )
            dataset_id = request.POST.get("train-dataset")

            # Populate choices
            if dataset_id:
                try:
                    dataset = Dataset.objects.get(
                        pk=dataset_id, uploaded_by=request.user
                    )
                    columns = (
                        list(dataset.columns.keys())
                        if isinstance(dataset.columns, dict)
                        else list(dataset.columns or [])
                    )
                    choices = [(c, c) for c in columns]
                    train_form.fields["target"].choices = choices
                    train_form.fields["features"].choices = choices
                except Dataset.DoesNotExist:
                    pass

            # Save current selections to re-display in the template/JS if there's an error
            selected_target = request.POST.get("train-target", "")
            selected_features = request.POST.getlist("train-features")

            if train_form.is_valid():
                data = train_form.cleaned_data
                hours = data.get("training_hours", 0)
                minutes = data.get("training_minutes", 0)
                time_limit_seconds = (hours * 3600) + (minutes * 60)

                new_model = MLModel.objects.create(
                    name=data["name"],
                    description=data["description"],
                    related_dataset=data["dataset"],
                    target=data["target"],
                    uploaded_by=request.user,
                    status="TRAINING",
                )
                train_autogluon_model.delay(
                    model_id=new_model.id,
                    dataset_id=data["dataset"].id,
                    target=data["target"],
                    features=data["features"],
                    time_limit=time_limit_seconds,
                    presets=data["presets"],
                )
                return redirect("manage_MLmodels_view")

    # Invalid GET or POST -> prepare forms
    upload_form = upload_form or UploadMLModelForm(prefix="upload", user=request.user)

    if train_form is None:
        # If ?train-dataset=ID came in GET, pre-populate choices
        dataset_id = request.GET.get("train-dataset")
        if dataset_id:
            try:
                dataset = Dataset.objects.get(pk=dataset_id, uploaded_by=request.user)
                columns = (
                    list(dataset.columns.keys())
                    if isinstance(dataset.columns, dict)
                    else list(dataset.columns or [])
                )
                choices = [(c, c) for c in columns]
                train_form = TrainMLModelForm(
                    prefix="train", initial={"dataset": dataset}, user=request.user
                )
                train_form.fields["target"].choices = choices
                train_form.fields["features"].choices = choices
            except Dataset.DoesNotExist:
                train_form = TrainMLModelForm(prefix="train", user=request.user)
        else:
            train_form = TrainMLModelForm(prefix="train", user=request.user)

    # Prepare JSON-friendly selected_features for use in the JS template
    selected_features_json = json.dumps(selected_features)

    # Filter models by the logged-in user
    models = MLModel.objects.filter(uploaded_by=request.user).order_by("-date")
    context = {
        "models": models,
        "upload_form": upload_form,
        "train_form": train_form,
        "selected_target": selected_target,
        "selected_features_json": selected_features_json,
    }
    return render(request, "manage_MLmodels.html", context)


@login_required
def delete_MLmodel(request, MLmodel_id):
    """
    Delete an ML model instance and its associated file.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id, uploaded_by=request.user)

    # If the model has an associated directory, remove it.
    if model_obj.file and model_obj.file.path and os.path.exists(model_obj.file.path):
        # Use shutil.rmtree for directories
        shutil.rmtree(model_obj.file.path, ignore_errors=True)
    model_obj.delete()

    return redirect("manage_MLmodels_view")


@login_required
def download_MLmodel(request, MLmodel_id):
    """
    Allow downloading the file associated with an ML model.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id, uploaded_by=request.user)
    if model_obj.file and os.path.exists(model_obj.file.path):
        base_dir = model_obj.file.path
        zip_root = base_dir

        # Auto-detect if there's a single directory inside the main one.
        dir_contents = os.listdir(base_dir)
        if len(dir_contents) == 1 and os.path.isdir(
            os.path.join(base_dir, dir_contents[0])
        ):
            zip_root = os.path.join(base_dir, dir_contents[0])

        # Create a zip file containing the entire directory
        zip_filename = f"{model_obj.name}.zip"

        # Create model_info.txt content
        info_content = (
            f"Model Name: {model_obj.name}\n"
            f"Description: {model_obj.description or 'N/A'}\n"
            f"Target Variable: {model_obj.target}\n"
        )
        if model_obj.features:
            features_str = ", ".join(model_obj.features)
            info_content += f"Features: {features_str}\n"
        else:
            info_content += "Features: N/A\n"

        info_content_bytes = info_content.encode("utf-8")

        # Create the zip in a temporary file to avoid conflicts
        tmp_zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(tmp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(zip_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, zip_root))

            # Add the model_info.txt file to the zip
            zipf.writestr("model_info.txt", info_content_bytes)

        # Read the zip file into memory
        with open(tmp_zip_path, "rb") as f:
            zip_data = f.read()
        os.remove(tmp_zip_path)

        response = HttpResponse(zip_data, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'

        return response

    raise Http404("File does not exist or was not found.")


@login_required
def visualize_MLmodel(request, MLmodel_id):
    """
    Display details and cached evaluation results for an ML model.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id, uploaded_by=request.user)
    # Get all test results to be listed in a dropdown
    # Assuming TestResult is linked to MLModel which is now user-specific
    test_results = model_obj.test_results.order_by("-test_date").all()

    context = {
        "model": model_obj,
        "test_results": test_results,
    }
    return render(request, "_visualize_MLmodel_details_partial.html", context)


@login_required
@require_GET
def get_leaderboard_data(request, result_id):
    """
    Returns leaderboard data for a specific test result as JSON.
    """

    # Ensure the user owns the model related to the test result
    test_result = get_object_or_404(
        TestResult, pk=result_id, model__uploaded_by=request.user
    )
    leaderboard_data = None

    if test_result and test_result.leaderboard_data:
        try:
            # Reconstruct the DataFrame from the 'split' dictionary format
            # The format is: {'index': [...], 'columns': [...], 'data': [[...], ...]}
            lb_dict = test_result.leaderboard_data
            df = pd.DataFrame(lb_dict["data"], columns=lb_dict["columns"])

            leaderboard_data = {
                "headers": [h.replace("_", " ") for h in df.columns.tolist()],
                "rows": df.values.tolist(),
            }
        except Exception:
            leaderboard_data = None

    return JsonResponse({"leaderboard_data": leaderboard_data})


@login_required
@require_GET
def get_MLmodel_row_partial(request, MLmodel_id):
    """
    Returns the HTML for a single model table row to enable live updates.
    """
    model = get_object_or_404(MLModel, id=MLmodel_id, uploaded_by=request.user)
    return render(request, "_MLmodel_row_partial.html", {"model": model})


@login_required
@require_GET
def get_model_details(request, model_id):
    """
    Returns JSON with the model's target column.
    """
    model = get_object_or_404(MLModel, pk=model_id, uploaded_by=request.user)
    return JsonResponse({"target": model.target, "features": model.features or []})
