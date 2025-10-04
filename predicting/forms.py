from django import forms

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class PredictionForm(forms.Form):
    """Form for selecting a model and a dataset for prediction."""

    model = forms.ModelChoiceField(
        queryset=MLModel.objects.filter(status="COMPLETED"),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Trained Model",
    )
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Dataset for Prediction",
    )
