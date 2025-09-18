import json
import os
import shutil
import tempfile
import zipfile

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from manage_datasets.models import Dataset

from .forms import TrainMLModelForm, UploadMLModelForm
from .models import MLModel
from .tasks import train_autogluon_model


@require_GET
def get_dataset_columns(request, dataset_id):
    """
    Returns JSON with dataset columns (list of strings).
    Handles different formats of dataset.columns (dict, list, etc.).
    """
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
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


def manage_MLmodels(request):
    """
    Version that:
     - populates target/features via GET?train-dataset=<id> (if used),
     - on submission with errors, retains selected values,
     - exposes selected_features/selected_target in the context for JS to reapply.
    """
    upload_form = None
    train_form = None
    selected_target = ""
    selected_features = []

    # POST handling
    if request.method == "POST":
        # Upload
        if "upload_model" in request.POST:
            upload_form = UploadMLModelForm(
                request.POST, request.FILES, prefix="upload"
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

                                # Copy the contents to the final destination
                                shutil.copytree(source_dir, final_model_dir)

                                MLModel.objects.create(
                                    name=model_name,
                                    description=upload_form.cleaned_data["description"],
                                    target=upload_form.cleaned_data["target"],
                                    file=model_storage_path,
                                    related_dataset=upload_form.cleaned_data[
                                        "related_dataset"
                                    ],
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
            train_form = TrainMLModelForm(request.POST, prefix="train")
            dataset_id = request.POST.get("train-dataset")

            # Populate choices
            if dataset_id:
                try:
                    dataset = Dataset.objects.get(pk=dataset_id)
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
                new_model = MLModel.objects.create(
                    name=data["name"],
                    related_dataset=data["dataset"],
                    target=data["target"],
                    uploaded_by=None,  # No user auth for now
                    status="TRAINING",
                )
                train_autogluon_model.delay(
                    model_id=new_model.id,
                    dataset_id=data["dataset"].id,
                    target=data["target"],
                    features=data["features"],
                    time_limit=data["time_limit"],
                    presets=data["presets"],
                )
                return redirect("manage_MLmodels_view")

    # Invalid GET or POST -> prepare forms
    upload_form = upload_form or UploadMLModelForm(prefix="upload")

    if train_form is None:
        # If ?train-dataset=ID came in GET, pre-populate choices
        dataset_id = request.GET.get("train-dataset")
        if dataset_id:
            try:
                dataset = Dataset.objects.get(pk=dataset_id)
                columns = (
                    list(dataset.columns.keys())
                    if isinstance(dataset.columns, dict)
                    else list(dataset.columns or [])
                )
                choices = [
                    (c, c) for c in columns
                ]  # Instantiate with the dataset's initial value to show the select already with a value
                train_form = TrainMLModelForm(
                    prefix="train", initial={"dataset": dataset}
                )
                train_form.fields["target"].choices = choices
                train_form.fields["features"].choices = choices
            except Dataset.DoesNotExist:
                train_form = TrainMLModelForm(prefix="train")
        else:
            train_form = TrainMLModelForm(prefix="train")

    # Prepare JSON-friendly selected_features for use in the JS template
    selected_features_json = json.dumps(selected_features)

    models = MLModel.objects.all().order_by("-date")
    context = {
        "models": models,
        "upload_form": upload_form,
        "train_form": train_form,
        "selected_target": selected_target,
        "selected_features_json": selected_features_json,
    }
    return render(request, "manage_MLmodels.html", context)


def delete_MLmodel(request, MLmodel_id):
    """
    Delete an ML model instance and its associated file.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id)

    # If the model has an associated directory, remove it.
    if model_obj.file and model_obj.file.path and os.path.exists(model_obj.file.path):
        # Use shutil.rmtree for directories
        shutil.rmtree(model_obj.file.path, ignore_errors=True)
    model_obj.delete()

    return redirect("manage_MLmodels_view")


def download_MLmodel(request, MLmodel_id):
    """
    Allow downloading the file associated with an ML model.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id)
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

        # Create the zip in a temporary file to avoid conflicts
        tmp_zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(tmp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(zip_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, zip_root))

        # Read the zip file into memory
        with open(tmp_zip_path, "rb") as f:
            zip_data = f.read()
        os.remove(tmp_zip_path)

        response = HttpResponse(zip_data, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'

        return response

    raise Http404("File does not exist or was not found.")


def visualize_MLmodel(request, MLmodel_id):
    """
    Display details and cached evaluation results for an ML model.
    """
    model_obj = get_object_or_404(MLModel, id=MLmodel_id)
    context = {"model": model_obj}
    return render(request, "_visualize_MLmodel_partial.html", context)
