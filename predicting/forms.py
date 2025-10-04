from django import forms

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


class PredictionForm(forms.Form):
    """Form for selecting a model and a dataset for prediction."""

    model = forms.ModelChoiceField(
        queryset=MLModel.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Trained Model",
    )
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select a Dataset for Prediction",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["model"].queryset = MLModel.objects.filter(
                uploaded_by=user, status="COMPLETED"
            )
            self.fields["dataset"].queryset = (
                Dataset.objects.filter(uploaded_by=user)
                .exclude(name="--manual-data--")
                .order_by("name")
            )


class ModelSelectionForm(forms.Form):
    """Form for selecting just a model."""

    model = forms.ModelChoiceField(
        queryset=MLModel.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_model_manual"}),
        label="Select a Trained Model",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["model"].queryset = MLModel.objects.filter(
                uploaded_by=user, status="COMPLETED"
            )


class ManualPredictionForm(forms.Form):
    """Base form for manual prediction, fields will be added dynamically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FeatureSelectionForm(forms.Form):
    """Form for selecting a single feature from a list."""

    feature = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Feature for X-Axis",
    )
    feature2 = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Feature for Y-Axis (optional)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        features = kwargs.pop("features", [])
        super().__init__(*args, **kwargs)
        feature_choices = [(f, f) for f in features]
        self.fields["feature"].choices = feature_choices

        # Add a "None" option for the optional second feature
        feature2_choices = [("", "-- None --")] + feature_choices
        self.fields["feature2"].choices = feature2_choices
