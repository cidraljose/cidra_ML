import os

import pandas as pd
from autogluon.tabular import TabularPredictor
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from manage_datasets.models import Dataset

from .models import MLModel


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

    try:
        dataset_instance = Dataset.objects.get(id=dataset_id)
        dataset_path = os.path.join(settings.DATASETS_DIR, dataset_instance.file.name)
        train_data = pd.read_csv(dataset_path)

        columns_to_use = features + [target]
        train_data = train_data[columns_to_use]

        model_slug = slugify(model_instance.name)
        model_name = f"{model_slug}_{model_instance.id}"
        model_path = os.path.join(settings.MEDIA_ROOT, "MLmodels", model_name)

        # Train the model
        predictor = TabularPredictor(path=model_path, label=target).fit(
            train_data=train_data, time_limit=time_limit, presets=presets
        )

        # Update the MLModel instance with the results
        model_instance.status = "COMPLETED"
        model_instance.file.name = os.path.join("MLmodels", model_name)
        model_instance.features = predictor.feature_metadata_in.get_features()
        model_instance.evaluation_metrics = predictor.leaderboard(silent=True).to_dict()
        model_instance.evaluation_date = timezone.now()

        # Clear description in case it was a retry of a failed task
        model_instance.description = ""
        model_instance.save()

    except Exception as e:
        # The model_instance is guaranteed to exist here.
        model_instance.status = "FAILED"
        model_instance.description = f"Training failed: {str(e)}"
        model_instance.save()
