import base64
import io
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from autogluon.tabular import TabularPredictor
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel

from .forms import FeatureSelectionForm, ModelSelectionForm, PredictionForm
from .models import PredictionResult


def predicting(request):
    if request.method == "POST":
        if "submit_dataset" in request.POST:
            dataset_form = PredictionForm(request.POST, prefix="dataset")
            if dataset_form.is_valid():
                try:
                    ml_model = dataset_form.cleaned_data["model"]
                    dataset = dataset_form.cleaned_data["dataset"]

                    # Load data and drop target column if it exists
                    input_data = pd.read_csv(dataset.file.path)
                    data_for_prediction = input_data.copy()
                    if ml_model.target in data_for_prediction.columns:
                        data_for_prediction = data_for_prediction.drop(
                            columns=[ml_model.target]
                        )

                    predictor = TabularPredictor.load(ml_model.file.path)
                    predictions = predictor.predict(data_for_prediction)

                    output_df = input_data.copy()
                    output_df[f"predicted_{ml_model.target}"] = predictions

                    csv_buffer = io.StringIO()
                    output_df.to_csv(csv_buffer, index=False)
                    csv_content = ContentFile(csv_buffer.getvalue().encode("utf-8"))

                    base_name, ext = os.path.splitext(
                        os.path.basename(dataset.file.name)
                    )
                    prediction_filename = f"{base_name}_predicted.csv"

                    result = PredictionResult(
                        model=ml_model,
                        dataset=dataset,
                    )
                    result.prediction_file.save(
                        prediction_filename, csv_content, save=True
                    )
                    messages.success(
                        request,
                        f"Prediction for '{dataset.name}' using '{ml_model.name}' is complete. See history for download.",
                    )
                    return redirect(reverse("predicting_view") + "#history-panel")
                except Exception as e:
                    messages.error(request, f"An error occurred during prediction: {e}")

        elif "submit_manual" in request.POST:
            try:
                model_id = request.POST.get("manual-model")
                ml_model = get_object_or_404(MLModel, pk=model_id)

                # Process multiple rows from POST data
                manual_data_rows = []
                row_count = 0
                if ml_model.features:
                    while f"{ml_model.features[0]}[{row_count}]" in request.POST:
                        row_count += 1

                for i in range(row_count):
                    row_data = {
                        feature: request.POST.get(f"{feature}[{i}]")
                        for feature in ml_model.features
                    }
                    manual_data_rows.append(row_data)

                if not manual_data_rows:
                    raise ValueError("No data submitted for manual prediction.")

                input_df = pd.DataFrame(manual_data_rows)

                predictor = TabularPredictor.load(ml_model.file.path)
                predictions = predictor.predict(input_df)

                output_df = input_df.copy()
                output_df[f"predicted_{ml_model.target}"] = predictions

                csv_buffer = io.StringIO()
                output_df.to_csv(csv_buffer, index=False)
                csv_content = ContentFile(csv_buffer.getvalue().encode("utf-8"))

                prediction_filename = f"manual_prediction_{ml_model.id}.csv"

                # Get or create a single placeholder dataset for all manual predictions.
                # This dataset will be excluded from the main list view.
                manual_placeholder_dataset, _ = Dataset.objects.get_or_create(
                    name="--manual-data--",
                    defaults={
                        "description": "A placeholder for results from manual predictions.",
                        "columns": {"info": "placeholder"},
                    },
                )

                result = PredictionResult(
                    model=ml_model, dataset=manual_placeholder_dataset
                )
                result.prediction_file.save(prediction_filename, csv_content, save=True)

                messages.success(
                    request,
                    f"Manual prediction using '{ml_model.name}' is complete. See history for download.",
                )
                return redirect(reverse("predicting_view") + "#history-panel")

            except Exception as e:
                messages.error(request, f"An error occurred during prediction: {e}")

    # This block runs for GET requests or if a POST fails validation
    dataset_form = PredictionForm(prefix="dataset")
    model_selection_form = ModelSelectionForm(prefix="manual")
    if request.method == "POST" and "submit_dataset" in request.POST:
        dataset_form = PredictionForm(
            request.POST, prefix="dataset"
        )  # Re-bind with errors

    history = PredictionResult.objects.select_related("model", "dataset").order_by(
        "-prediction_date"
    )

    context = {
        "dataset_form": dataset_form,
        "model_selection_form": model_selection_form,
        "history": history,
    }
    return render(request, "predicting.html", context)


def visualize_prediction(request, result_id):
    """
    Generates and displays a plot of a selected feature vs. the prediction.
    """
    result = get_object_or_404(PredictionResult, pk=result_id)
    ml_model = result.model
    plot_data = None

    # Get features from the model, excluding the target variable
    features = [f for f in ml_model.features if f != ml_model.target]

    if request.method == "POST":
        form = FeatureSelectionForm(request.POST, features=features)
        if form.is_valid():
            selected_feature = form.cleaned_data["feature"]
            selected_feature2 = form.cleaned_data.get("feature2")
            try:
                # Read the prediction data from the stored file
                prediction_df = pd.read_csv(result.prediction_file.path)
                predicted_column = f"predicted_{ml_model.target}"

                # Ensure required columns exist
                if (
                    selected_feature not in prediction_df.columns
                    or (
                        selected_feature2
                        and selected_feature2 not in prediction_df.columns
                    )
                    or predicted_column not in prediction_df.columns
                ):
                    raise ValueError("Selected feature or prediction column not found.")

                # Generate plot
                fig = plt.figure(figsize=(10, 7))

                if selected_feature2:
                    # 3D Plot
                    ax = fig.add_subplot(111, projection="3d")
                    scatter = ax.scatter(
                        prediction_df[selected_feature],
                        prediction_df[selected_feature2],
                        prediction_df[predicted_column],
                        c=prediction_df[predicted_column],
                        cmap="viridis",
                    )
                    # Add a color bar which acts as a legend for the colors
                    cbar = fig.colorbar(scatter, shrink=0.35, aspect=20)
                    cbar.set_label(predicted_column)
                    ax.set_xlabel(selected_feature)
                    ax.set_ylabel(selected_feature2)
                    ax.set_zlabel(predicted_column)
                else:
                    # 2D Plot
                    sns.scatterplot(
                        data=prediction_df, x=selected_feature, y=predicted_column
                    )
                    plt.xlabel(selected_feature)
                    plt.ylabel(predicted_column)

                fig.tight_layout()
                plt.grid(True)

                # Save plot to a memory buffer and encode as base64
                buf = io.BytesIO()
                plt.savefig(buf, format="png", bbox_inches="tight")
                plot_data = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close()

            except Exception as e:
                messages.error(
                    request, f"An error occurred while generating the plot: {e}"
                )
    else:
        form = FeatureSelectionForm(features=features)

    context = {"form": form, "result": result, "plot_data": plot_data}
    return render(request, "_visualize_prediction.html", context)


@require_GET
def get_model_features(request, model_id):
    """
    Returns the features of a given model as JSON.
    """
    model = get_object_or_404(MLModel, pk=model_id)
    try:
        features = model.features
        return JsonResponse({"features": features})
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


def download_prediction_file(request, result_id):
    """
    Downloads the CSV file containing the original data plus the predictions.
    """
    result = get_object_or_404(PredictionResult, pk=result_id)
    if not result.prediction_file:
        raise Http404("Prediction file not found.")

    response = HttpResponse(result.prediction_file, content_type="text/csv")
    response["Content-Disposition"] = (
        f"attachment; filename={os.path.basename(result.prediction_file.name)}"
    )
    return response


def delete_prediction_result(request, result_id):
    """
    Deletes a prediction result instance and its associated file.
    """
    if request.method == "POST":
        result = get_object_or_404(PredictionResult, pk=result_id)
        result.prediction_file.delete(save=False)  # Delete file from storage
        result.delete()
        messages.success(request, "The prediction result has been deleted.")
        return redirect(reverse("predicting_view") + "#history-panel")
    raise Http404()
