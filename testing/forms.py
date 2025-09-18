import pandas as pd
from django import forms

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class TestingForm(forms.Form):
    # Field to select a trained model
    model = forms.ModelChoiceField(
        queryset=MLModel.objects.all(),
        label="Select Model to Test",
        empty_label="---------",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # Field to select the dataset for testing
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all(),
        label="Select Test Dataset",
        empty_label="---------",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # The target column will be dynamically populated using JavaScript
    target = forms.ChoiceField(
        label="Target Column",
        choices=[],
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="This must match the target column the model was trained on.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For POST requests, we need to populate the 'target' choices
        if self.is_bound and "dataset" in self.data:
            try:
                dataset_id = int(self.data.get("dataset"))
                dataset = Dataset.objects.get(pk=dataset_id)
                # Assuming the Dataset model has a 'file' attribute
                df = pd.read_csv(dataset.file.path)
                column_choices = [(col, col) for col in df.columns]
                self.fields["target"].choices = column_choices
            except (ValueError, TypeError, Dataset.DoesNotExist):
                pass
