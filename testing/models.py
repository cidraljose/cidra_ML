from django.db import models

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class TestResult(models.Model):
    """Stores the result of a single model evaluation on a dataset."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="test_results"
    )
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="test_results"
    )
    evaluation_metrics = models.JSONField()
    predictions = models.JSONField(null=True, blank=True)
    plot = models.TextField(null=True, blank=True)  # Store plot as base64 string
    test_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"Test of {self.model.name} on {self.dataset.name} at {self.test_date}"
