from django.contrib.auth.models import User
from django.db import models


class MLModel(models.Model):
    """Model to store machine learning models uploaded by users."""

    # Attributes that can be filled by user on form
    file = models.FileField(
        upload_to="MLmodels/",
        help_text="The ZIP file containing the model on Autogluon format",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, help_text="Name of the model")
    description = models.TextField(
        blank=True,
        null=True,
        help_text="A brief description about the model and it's purpouse",
    )
    related_dataset = models.ForeignKey(
        "manage_datasets.Dataset", on_delete=models.SET_NULL, null=True, blank=True
    )
    features = models.JSONField(
        help_text="List of features used by the model", blank=True, null=True
    )
    target = models.CharField(max_length=100, help_text="Target variable name")
    model_type = models.CharField(
        max_length=100,
        default="TabularPredictor",
        help_text="Type of model, e.g., TabularPredictor",
    )

    # Attributes filled automatically
    STATUS_CHOICES = [
        ("TRAINING", "Training"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="COMPLETED",
        help_text="The current status of the model.",
    )
    date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the dataset was uploaded"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="User who uploaded the model",
    )

    # Attributes filled after model evaluation
    is_evaluated = models.BooleanField(
        default=False, help_text="Indicates if the model has been evaluated."
    )
    evaluation_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time when the model was last evaluated.",
    )
    evaluation_metrics = models.JSONField(
        blank=True,
        null=True,
        help_text="Key-value pairs of evaluation metrics (e.g., accuracy, F1-score).",
    )
    evaluation_plots = models.JSONField(
        blank=True,
        null=True,
        help_text="Cached plots from model evaluation or prediction simulations.",
    )

    def __str__(self):
        return self.name
