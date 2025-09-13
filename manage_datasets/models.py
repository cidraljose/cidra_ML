"""Models for manage_datasets"""

from django.contrib.auth.models import User
from django.db import models


class Dataset(models.Model):
    """
    Modelo para armazenamento de datasets
    """

    # Atribute filled by user on form
    file = models.FileField(
        upload_to="datasets/", help_text="The CSV file containing the dataset"
    )
    name = models.CharField(max_length=100, help_text="Name of the dataset")
    separator = models.CharField(
        max_length=10,
        default=",",
        help_text="Separator used in the CSV file (e.g., ',', ';', '\t')",
    )
    encoding = models.CharField(
        max_length=20,
        default="utf-8",
        help_text="Encoding of the CSV file (e.g., 'utf-8', 'latin-1')",
    )
    description = models.TextField(
        blank=True, null=True, help_text="A brief description of the dataset's contents"
    )

    # Atribues filled automatically
    date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the dataset was uploaded"
    )
    n_rows = models.IntegerField(default=0, help_text="Number of rows in the dataset")
    columns = models.JSONField(
        help_text="JSON representation of the column names and their data types"
    )
    n_columns = models.IntegerField(
        default=0, help_text="Number of columns in the dataset"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="User who uploaded the dataset",
    )

    def __str__(self):
        return str(self.name)
