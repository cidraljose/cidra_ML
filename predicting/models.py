from django.db import models

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class PredictionResult(models.Model):
    """Stores the result of a prediction task."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="prediction_results"
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.SET_NULL,
        related_name="prediction_results",
        null=True,
        blank=True,
    )
    prediction_file = models.FileField(upload_to="predictions/")
    prediction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.model.name} on {self.dataset.name}"
