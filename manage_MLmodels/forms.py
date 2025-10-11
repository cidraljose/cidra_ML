"""Forms for the manage_MLmodels app"""

from django import forms

from manage_datasets.models import Dataset


class UploadMLModelForm(forms.Form):
    """Form for uploading machine learning models."""

    name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    target = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    features = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text="Comma-separated list of feature names. Will be auto-filled if found in the model.",
    )
    file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control"}))
    related_dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(),
        required=False,
        empty_label="Select a related dataset (optional)",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["related_dataset"].queryset = (
                Dataset.objects.filter(
                    uploaded_by=user,
                )
                .exclude(name="--manual-data--")
                .order_by("name")
            )


class TrainMLModelForm(forms.Form):
    """Form for training a new machine learning model."""

    PRESET_CHOICES = [
        ("medium_quality", "Medium Quality (Fast)"),
        ("good_quality", "Good Quality"),
        ("high_quality", "High Quality"),
        ("best_quality", "Best Quality (Slow)"),
    ]

    name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(),
        empty_label="Select a dataset to train on",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    target = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Select the column you want to predict.",
    )
    features = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
        help_text="Select the columns to use for training. (Ctrl+Click for multiple)",
    )
    training_hours = forms.IntegerField(
        label="Training Time Limit (Hours)",
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Set to 0 for no limit (if minutes is also 0).",
    )
    training_minutes = forms.IntegerField(
        label="Training Time Limit (Minutes)",
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Value from 0 to 59.",
    )
    presets = forms.ChoiceField(
        choices=PRESET_CHOICES,
        initial="medium_quality",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["dataset"].queryset = (
                Dataset.objects.filter(
                    uploaded_by=user,
                )
                .exclude(name="--manual-data--")
                .order_by("name")
            )
