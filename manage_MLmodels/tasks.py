# celery -A cidra_ML worker -l info -P solo
import os
import sys
import time
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


@shared_task
def train_autogluon_model(model_id, dataset_id, target, features, time_limit, presets):
    """
    A Celery task to train an AutoGluon model in the background.
    """

    # Ensure the MLModel instance exists
    try:
        model_instance = MLModel.objects.get(id=model_id)
    except MLModel.DoesNotExist:
        print(f"MLModel with id={model_id} not found. Aborting training task.")
        return

    if time_limit == 0:
        time_limit = None

    # Temporarily restore stdout/stderr to prevent 'fileno' error with ray/celery on Windows
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    try:
        dataset_instance = Dataset.objects.get(id=dataset_id)
        train_data = pd.read_csv(dataset_instance.file.path)

        # Ensure only selected features and the target are used for training
        if features:
            features = [f for f in features if f != target]
            columns_to_use = features + [target]
            train_data = train_data[columns_to_use]

        model_slug = slugify(model_instance.name)
        model_name = f"{model_slug}_{model_instance.id}"
        model_path = os.path.join(settings.MEDIA_ROOT, "MLmodels", model_name)

        # Train the model
        start_time = time.time()
        predictor = TabularPredictor(path=model_path, label=target).fit(
            train_data=train_data,
            time_limit=time_limit,
            presets=presets,
        )
        end_time = time.time()
        duration_seconds = end_time - start_time

        # Update the MLModel instance with the results
        model_instance.status = "COMPLETED"
        model_instance.file.name = os.path.join("MLmodels", model_name)
        model_instance.training_duration = timedelta(seconds=duration_seconds)
        model_instance.features = predictor.feature_metadata_in.get_features()

        # Reset index to make 'model' a column before saving
        leaderboard_df = predictor.leaderboard(silent=True).reset_index()
        model_instance.evaluation_metrics = leaderboard_df.to_dict()
        model_instance.evaluation_date = timezone.now()

        # Clear description in case it was a retry of a failed task
        model_instance.description = ""
        model_instance.save()

    except Exception as e:
        # The model_instance is guaranteed to exist here.
        model_instance.status = "FAILED"
        model_instance.description = f"Training failed: {str(e)}"
        model_instance.save()
    finally:
        # Always restore the original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
