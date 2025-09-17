"""
Forms for manage_datasets app
"""

from django import forms


class UploadCSVForm(forms.Form):
    """
    Form for uploading CSV datasets.
    """

    file = forms.FileField(label="Arquivo CSV")
    name = forms.CharField(label="Nome do conjunto de dados", max_length=64)
    separator = forms.ChoiceField(
        choices=[
            (",", "Vírgula ( , )"),
            (";", "Ponto e vírgula ( ; )"),
            ("|", "Barra vertical ( | )"),
            ("\\t", "Tabulação ( \\t )"),
        ],
        label="Separador",
    )
    encoding = forms.ChoiceField(
        choices=[
            ("utf-8", "UTF-8"),
            ("latin-1", "Latin-1"),
            ("iso-8859-1", "ISO-8859-1"),
            ("cp1252", "CP1252"),
        ],
        label="Codificação",
        initial="utf-8",
    )
    description = forms.CharField(
        label="Descrição",
        max_length=512,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        required=False,
    )
