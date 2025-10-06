# celery -A cidra_ML worker -l info -P solo
import logging
import os
import sys
import time
import traceback
from datetime import timedelta

import pandas as pd
from autogluon.tabular import TabularPredictor
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from manage_datasets.models import Dataset

from .models import MLModel

CELERY_WORKER_REDIRECT_STDOUTS = False

logger = logging.getLogger(__name__)


@shared_task
def train_autogluon_model(model_id, dataset_id, target, features, time_limit, presets):
    """
    A Celery task to train an AutoGluon model in the background.
    """

    # Ensure the MLModel instance exists
    logger.info(f"Starting training task for MLModel ID: {model_id}")
    try:
        model_instance = MLModel.objects.get(id=model_id)
    except MLModel.DoesNotExist:
        logger.error(f"MLModel with id={model_id} not found. Aborting training task.")
        return

    if time_limit == 0:
        time_limit = None

    # Temporarily restore stdout/stderr to prevent 'fileno' error with ray/celery on Windows
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    try:
        logger.info(f"Fetching dataset ID: {dataset_id}")
        dataset_instance = Dataset.objects.get(id=dataset_id)
        train_data = pd.read_csv(dataset_instance.file.path)
        logger.info("Dataset loaded successfully.")

        # Ensure only selected features and the target are used for training
        if features:
            logger.info("Filtering dataset to selected features.")
            features = [f for f in features if f != target]
            columns_to_use = features + [target]
            train_data = train_data[columns_to_use]

        model_slug = slugify(model_instance.name)
        model_name = f"{model_slug}_{model_instance.id}"
        model_path = os.path.join(settings.MEDIA_ROOT, "MLmodels", model_name)
        logger.info(f"Model will be saved to: {model_path}")

        # Train the model
        logger.info("Starting AutoGluon predictor.fit()...")
        start_time = time.time()
        predictor = TabularPredictor(path=model_path, label=target).fit(
            train_data=train_data,
            time_limit=time_limit,
            presets=presets,
        )
        end_time = time.time()
        duration_seconds = end_time - start_time
        logger.info("Model training complete.")

        # Update the MLModel instance with the results
        logger.info("Updating model instance in the database...")
        model_instance.status = "COMPLETED"
        model_instance.file.name = os.path.join("MLmodels", model_name)
        model_instance.training_duration = timedelta(seconds=duration_seconds)
        model_instance.features = predictor.feature_metadata_in.get_features()

        # Reset index to make 'model' a column before saving
        logger.info("Generating and saving leaderboard...")
        leaderboard_df = predictor.leaderboard(silent=True).reset_index()
        model_instance.evaluation_metrics = leaderboard_df.to_dict()
        model_instance.evaluation_date = timezone.now()

        # Preserve the original description
        model_instance.save()
        logger.info(f"Task for MLModel ID: {model_id} completed successfully.")

    except Exception as e:
        # The model_instance is guaranteed to exist here.
        logger.error(
            f"An error occurred during training for MLModel ID: {model_id}. Error: {e}"
        )
        error_trace = traceback.format_exc()
        model_instance.status = "FAILED"
        # Store the detailed error in the description field for debugging
        model_instance.description = (
            f"Training failed: {str(e)}\n\nTraceback:\n{error_trace}"
        )
        model_instance.save()
    finally:
        # Always restore the original stdout/stderr
        logger.info("Restoring stdout/stderr.")
        sys.stdout = original_stdout
        sys.stderr = original_stderr
