from django.db import models

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class PredictionResult(models.Model):
    """Stores the result of a single prediction run."""

    STATUS_PENDING = "PENDING"
    STATUS_RUNNING = "RUNNING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="prediction_results"
    )
    dataset = models.ForeignKey(
        Dataset, on_delete=models.SET_NULL, null=True, blank=True
    )
    prediction_file = models.FileField(upload_to="predictions/", null=True, blank=True)
    prediction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    error_message = models.TextField(blank=True, null=True)
