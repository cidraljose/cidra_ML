# celery -A cidra_ML worker -l info -P solo
import io

import pandas as pd
from autogluon.tabular import TabularPredictor
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import TestingForm
from .models import TestResult
from .tasks import evaluate_model_task

CELERY_WORKER_REDIRECT_STDOUTS = False


@login_required
def testing(request):
    form = TestingForm(user=request.user)
    selected_target = ""
    selected_model_id = ""
    selected_features_json = "[]"

    if request.method == "POST":
        form = TestingForm(request.POST, user=request.user)
        if form.is_valid():
            ml_model = form.cleaned_data["model"]
            dataset = form.cleaned_data["dataset"]

            try:
                # Create a TestResult instance with PENDING status
                test_result = TestResult.objects.create(
                    model=ml_model,
                    dataset=dataset,
                    status=TestResult.STATUS_PENDING,
                )
                # Dispatch the background task only after the transaction is committed
                transaction.on_commit(lambda: evaluate_model_task.delay(test_result.id))

                messages.success(
                    request,
                    f"Evaluation of '{ml_model.name}' on '{dataset.name}' has started. Results will appear in the history.",
                )
                return redirect(reverse("testing_view") + "#history-panel")

            except Exception as e:
                messages.error(request, f"An error occurred during evaluation: {e}")
        else:
            # Preserve selections on form error
            selected_target = request.POST.get("target", "")
            selected_model_id = request.POST.get("model", "")
            messages.error(request, "Please correct the errors below.")

    history = TestResult.objects.filter(model__uploaded_by=request.user).select_related(
        "model", "dataset"
    )

    context = {
        "form": form,
        "selected_target": selected_target,
        "selected_model_id": selected_model_id,
        "selected_features_json": selected_features_json,
        "history": history,
    }
    return render(request, "testing.html", context)


@login_required
@require_GET
def get_test_result_details(request, result_id):
    """
    Returns the evaluation metrics and plot for a specific test result.
    """
    result = get_object_or_404(
        TestResult, pk=result_id, model__uploaded_by=request.user
    )
    leaderboard_payload = None
    if result.leaderboard_data and "columns" in result.leaderboard_data:
        leaderboard_payload = {
            "headers": result.leaderboard_data["columns"],
            "rows": result.leaderboard_data["data"],
            "scores": [row[1] for row in result.leaderboard_data["data"]],
            "model_names": [row[0] for row in result.leaderboard_data["data"]],
        }
    return JsonResponse(
        {
            "metrics": result.evaluation_metrics,
            "leaderboard": leaderboard_payload,
            "plot": result.plot,
            "model_name": result.model.name,
            "dataset_name": result.dataset.name,
        }
    )


@login_required
def download_test_with_predictions(request, result_id):
    """
    Downloads the test dataset with an added 'y_predicted' column.
    """
    result = get_object_or_404(
        TestResult, pk=result_id, model__uploaded_by=request.user
    )

    if not result.predictions:
        raise Http404("Predictions are not available for this test result.")

    try:
        # Read the original dataset
        df = pd.read_csv(result.dataset.file.path)

        # Add the predictions as a new column
        df[f"{result.model.target}_predicted"] = result.predictions

        # Create an in-memory CSV file
        output = io.StringIO()
        df.to_csv(output, index=False)
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename={result.dataset.name}_with_predictions.csv"
        )
        return response

    except FileNotFoundError:
        raise Http404("The original dataset file could not be found.")
    except Exception as e:
        raise Http404(f"An error occurred while preparing the download: {e}")


@login_required
def delete_test_result(request, result_id):
    """
    Deletes a test result instance.
    """
    if request.method == "POST":
        result = get_object_or_404(
            TestResult, pk=result_id, model__uploaded_by=request.user
        )
        model = result.model

        # Delete the test result object
        result.delete()

        # Clear evaluation fields on the related model
        model.is_evaluated = False
        model.evaluation_date = None
        model.evaluation_plots = None
        model.save()

        # Redirect back to the testing page with a hash to open the history tab
        return redirect(reverse("testing_view") + "#history-panel")
    raise Http404()


@login_required
@require_GET
def get_test_result_row_partial(request, result_id):
    """
    Returns the HTML for a single test result table row to enable live updates.
    """
    result = get_object_or_404(
        TestResult, pk=result_id, model__uploaded_by=request.user
    )
    return render(request, "_test_result_row_partial.html", {"result": result})
