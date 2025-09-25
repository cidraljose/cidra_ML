import pandas as pd
from django import forms

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class TestingForm(forms.Form):
    # Field to select a trained model
    model = forms.ModelChoiceField(
        queryset=MLModel.objects.all(),
        label="Select Model to Test",
        empty_label="--",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # Field to select the dataset for testing
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all(),
        label="Select Test Dataset",
        empty_label="--",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        model = cleaned_data.get("model")
        dataset = cleaned_data.get("dataset")

        if model and dataset:
            target_column = model.target
            if not target_column:
                raise forms.ValidationError(
                    "The selected model does not have a target column defined."
                )

            try:
                # Read only the header to check for the column
                df_header = pd.read_csv(dataset.file.path, nrows=0)
                if target_column not in df_header.columns:
                    raise forms.ValidationError(
                        f"The selected dataset '{dataset.name}' does not contain the required target column ('{target_column}') for the model '{model.name}'."
                    )
            except Exception as e:
                raise forms.ValidationError(
                    f"Could not read the dataset file. Error: {e}"
                )
        return cleaned_data
