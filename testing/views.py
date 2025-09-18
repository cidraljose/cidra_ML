import pandas as pd
from autogluon.tabular import TabularPredictor
from django.contrib import messages
from django.shortcuts import render

from .forms import TestingForm


def testing(request):
    form = TestingForm()
    evaluation_results = None
    selected_target = ""
    selected_features_json = "[]"

    if request.method == "POST":
        form = TestingForm(request.POST)
        if form.is_valid():
            ml_model = form.cleaned_data["model"]
            dataset = form.cleaned_data["dataset"]
            target_column = form.cleaned_data["target"]

            try:
                test_data = pd.read_csv(dataset.file.path)
                predictor = TabularPredictor.load(ml_model.model_path)

                # Evaluate the model
                evaluation_results = predictor.evaluate(test_data, label=target_column)

                # leaderboard = predictor.leaderboard(test_data)

                messages.success(
                    request,
                    f"Model '{ml_model.name}' evaluated successfully on '{dataset.name}'.",
                )

            except Exception as e:
                messages.error(request, f"An error occurred during evaluation: {e}")
        else:
            # Preserve selections on form error
            selected_target = request.POST.get("target", "")
            messages.error(request, "Please correct the errors below.")

    context = {
        "form": form,
        "evaluation_results": evaluation_results,
        "selected_target": selected_target,
        "selected_features_json": selected_features_json,
    }
    return render(request, "testing.html", context)
