from django import forms

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class TestingForm(forms.Form):
    """Form for selecting a model and a dataset for testing."""

    model = forms.ModelChoiceField(
        queryset=MLModel.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Trained Model to Evaluate",
    )
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Dataset for Testing",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["model"].queryset = MLModel.objects.filter(
                uploaded_by=user, status="COMPLETED"
            )
            self.fields["dataset"].queryset = Dataset.objects.filter(
                uploaded_by=user
            ).exclude(name="--manual-data--")
