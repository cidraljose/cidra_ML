"""
Forms for manage_datasets app
"""

from django import forms

from .models import Dataset


class UploadCSVForm(forms.Form):
    """
    Form for uploading CSV datasets.
    """

    file = forms.FileField(label="CSV File")
    name = forms.CharField(label="Dataset Name", max_length=64)
    separator = forms.ChoiceField(
        choices=[
            (",", "Comma ( , )"),
            (";", "Semicolon ( ; )"),
            ("|", "Pipe ( | )"),
            ("\\t", "Tab ( \\t )"),
        ],
        label="Separator",
    )
    encoding = forms.ChoiceField(
        choices=[
            ("utf-8", "UTF-8"),
            ("latin-1", "Latin-1"),
            ("iso-8859-1", "ISO-8859-1"),
            ("cp1252", "CP1252"),
        ],
        label="Encoding",
        initial="utf-8",
    )
    description = forms.CharField(
        label="Description",
        max_length=512,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        required=False,
    )


class SplitDatasetForm(forms.Form):
    """
    Form for splitting a dataset into training and testing sets.
    """

    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all().order_by("-date"),
        label="Select Dataset to Split",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    train_split_ratio = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=80,
        label="Training Set Ratio (%)",
        help_text="The percentage of data for the training set. The rest will be for the test set.",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
