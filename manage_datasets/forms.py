from django import forms

from .models import Dataset


class UploadCSVForm(forms.Form):
    """Form for uploading a new CSV dataset."""

    name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control"}))
    encoding = forms.ChoiceField(
        choices=[("utf-8", "UTF-8"), ("latin-1", "Latin-1")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    separator = forms.ChoiceField(
        choices=[(",", "Comma (,)"), (";", "Semicolon (;)"), ("\\t", "Tab")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class SplitDatasetForm(forms.Form):
    """Form for splitting a dataset."""

    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Select Dataset to Split",
    )
    train_split_ratio = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=70,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        label="Training Set Ratio (%)",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["dataset"].queryset = Dataset.objects.filter(
                uploaded_by=user
            ).exclude(name="--manual-data--")


class MergeDatasetsForm(forms.Form):
    """Form for merging multiple datasets."""

    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
        label="Select Datasets to Merge",
    )
    new_dataset_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Name for Merged Dataset",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["datasets"].queryset = Dataset.objects.filter(
                uploaded_by=user
            ).exclude(name="--manual-data--")
