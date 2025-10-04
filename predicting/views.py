import io
import os

import pandas as pd
from autogluon.tabular import TabularPredictor
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import PredictionForm
from .models import PredictionResult


def predicting(request):
    form = PredictionForm()

    if request.method == "POST":
        form = PredictionForm(request.POST)
        if form.is_valid():
            ml_model = form.cleaned_data["model"]
            dataset = form.cleaned_data["dataset"]

            try:
                # Load data and drop target column if it exists
                input_data = pd.read_csv(dataset.file.path)
                data_for_prediction = input_data
                if ml_model.target in data_for_prediction.columns:
                    data_for_prediction = data_for_prediction.drop(
                        columns=[ml_model.target]
                    )

                # Load model and generate predictions
                predictor = TabularPredictor.load(ml_model.file.path)
                predictions = predictor.predict(data_for_prediction)

                # Add predictions to a new column
                output_df = input_data.copy()
                output_df[f"predicted_{ml_model.target}"] = predictions

                # Save the new dataframe to a CSV in memory
                csv_buffer = io.StringIO()
                output_df.to_csv(csv_buffer, index=False)
                csv_content = ContentFile(csv_buffer.getvalue().encode("utf-8"))

                # Create a filename for the prediction output
                base_name, ext = os.path.splitext(os.path.basename(dataset.file.name))
                prediction_filename = f"{base_name}_predicted.csv"

                # Create and save the PredictionResult instance
                result = PredictionResult(
                    model=ml_model,
                    dataset=dataset,
                )
                result.prediction_file.save(prediction_filename, csv_content, save=True)

                messages.success(
                    request,
                    f"Prediction for '{dataset.name}' using '{ml_model.name}' is complete. See history for download.",
                )
                return redirect(reverse("predicting_view") + "#history-panel")

            except Exception as e:
                messages.error(request, f"An error occurred during prediction: {e}")
        else:
            messages.error(request, "Please correct the errors below.")

    history = PredictionResult.objects.select_related("model", "dataset").order_by(
        "-prediction_date"
    )

    context = {
        "form": form,
        "history": history,
    }
    return render(request, "predicting.html", context)


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
