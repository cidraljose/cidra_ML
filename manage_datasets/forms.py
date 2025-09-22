"""
Forms for manage_datasets app
"""

from django import forms


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
