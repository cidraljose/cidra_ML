# celery -A cidra_ML worker -l info -P solo
import base64
import logging
import sys
import traceback
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from autogluon.tabular import TabularPredictor
from celery import shared_task

from .models import TestResult

logger = logging.getLogger(__name__)


@shared_task
def evaluate_model_task(result_id):
    """
    Celery task to evaluate a model on a dataset asynchronously.
    """
    # Temporarily restore stdout/stderr to prevent 'fileno' error with ray/celery on Windows
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    try:
        logger.info(f"Starting evaluation for TestResult ID: {result_id}")
        result = TestResult.objects.get(id=result_id)
        result.status = TestResult.STATUS_RUNNING
        result.save()

        try:
            logger.info("Fetching model and dataset...")
            ml_model = result.model
            dataset = result.dataset
            logger.info("Model and dataset fetched successfully.")

            logger.info(f"Reading dataset from: {dataset.file.path}")
            test_data = pd.read_csv(dataset.file.path)
            logger.info("Dataset loaded successfully.")

            logger.info(f"Loading predictor from: {ml_model.file.path}")
            predictor = TabularPredictor.load(path=ml_model.file.path)
            logger.info("Predictor loaded successfully.")

            logger.info("Starting model evaluation...")
            evaluation_results = predictor.evaluate(test_data)
            logger.info("Evaluation complete.")

            logger.info("Generating leaderboard and predictions for plot...")
            leaderboard_df = predictor.leaderboard(test_data, silent=True).reset_index()
            predictions = predictor.predict(test_data.drop(columns=[ml_model.target]))
            logger.info("Leaderboard and predictions generated.")

            real_values = test_data[ml_model.target]
            evaluation_plot = create_predicted_vs_real_plot(real_values, predictions)
            logger.info("Plot generated.")

            logger.info("Saving results to database...")
            result.evaluation_metrics = evaluation_results
            result.predictions = predictions.tolist()
            result.leaderboard_data = leaderboard_df.to_dict("split")
            result.plot = evaluation_plot
            result.status = TestResult.STATUS_COMPLETED
            result.save()
            logger.info(f"Task for TestResult ID: {result_id} completed successfully.")

        except Exception as e:
            logger.error(
                f"An error occurred during evaluation for TestResult ID: {result_id}. Error: {e}"
            )
            error_trace = traceback.format_exc()
            result.status = TestResult.STATUS_FAILED
            result.evaluation_metrics = {"error": str(e), "traceback": error_trace}
            result.save()

    finally:
        # Restore the original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def create_predicted_vs_real_plot(y_true, y_pred):
    """
    Generates a scatter plot of predicted vs. real values.

    Args:
        y_true (pd.Series): The actual target values.
        y_pred (pd.Series): The values predicted by the model.

    Returns:
        str: A base64 encoded string of the plot image, or None if data is not numeric.
    """
    # Ensure data is numeric for plotting
    if not pd.api.types.is_numeric_dtype(y_true) or not pd.api.types.is_numeric_dtype(
        y_pred
    ):
        return None

    plt.figure(figsize=(8, 6))
    ax = sns.scatterplot(x=y_true, y=y_pred)
    ax.set_xlabel("Real Values")
    ax.set_ylabel("Predicted Values")

    # Add a line for perfect predictions (y=x)
    lims = [
        min(ax.get_xlim()[0], ax.get_ylim()[0]),  # min of both axes
        max(ax.get_xlim()[1], ax.get_ylim()[1]),  # max of both axes
    ]
    ax.plot(lims, lims, "r--", alpha=0.75, zorder=0)
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode("utf-8")
