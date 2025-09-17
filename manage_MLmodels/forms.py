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
    file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control"}))
    related_dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all().order_by("name"),
        required=False,
        empty_label="Select a related dataset (optional)",
        widget=forms.Select(attrs={"class": "form-select"}),
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
    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all().order_by("name"),
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
    time_limit = forms.IntegerField(
        label="Max Training Time (seconds)",
        min_value=60,
        initial=60,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    presets = forms.ChoiceField(
        choices=PRESET_CHOICES,
        initial="medium_quality",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
