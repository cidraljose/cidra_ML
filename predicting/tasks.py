import io
import logging
import os
import traceback

import pandas as pd
from autogluon.tabular import TabularPredictor
from celery import shared_task
from django.core.files.base import ContentFile

from .models import PredictionResult

logger = logging.getLogger(__name__)


@shared_task
def run_prediction_task(result_id, manual_data_rows=None):
    """
    Celery task to run predictions on a dataset or manual data.
    """
    try:
        logger.info(f"Starting prediction for PredictionResult ID: {result_id}")
        result = PredictionResult.objects.get(id=result_id)
        result.status = PredictionResult.STATUS_RUNNING
        result.save()

        ml_model = result.model
        predictor = TabularPredictor.load(ml_model.file.path)

        if manual_data_rows:
            input_df = pd.DataFrame(manual_data_rows)
            data_for_prediction = input_df.copy()
            prediction_filename = f"manual_prediction_{ml_model.id}_{result.id}.csv"
        else:
            input_df = pd.read_csv(result.dataset.file.path)
            data_for_prediction = input_df.copy()
            if ml_model.target in data_for_prediction.columns:
                data_for_prediction = data_for_prediction.drop(
                    columns=[ml_model.target]
                )
            base_name, _ = os.path.splitext(os.path.basename(result.dataset.file.name))
            prediction_filename = f"{base_name}_predicted.csv"

        predictions = predictor.predict(data_for_prediction)

        output_df = input_df.copy()
        output_df[f"predicted_{ml_model.target}"] = predictions

        csv_buffer = io.StringIO()
        output_df.to_csv(csv_buffer, index=False)
        csv_content = ContentFile(csv_buffer.getvalue().encode("utf-8"))

        result.prediction_file.save(prediction_filename, csv_content, save=False)
        result.status = PredictionResult.STATUS_COMPLETED
        result.save()
        logger.info(f"Prediction task for ID {result_id} completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during prediction for ID {result_id}: {e}")
        result.status = PredictionResult.STATUS_FAILED
        result.error_message = traceback.format_exc()
        result.save()
