from django.contrib import admin
from django.contrib.auth.models import Group, User

from manage_datasets.models import Dataset
from manage_MLmodels.models import MLModel


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    """Admin configuration for MLModel."""

    list_display = ("name", "status", "uploaded_by", "date", "related_dataset")
    list_filter = ("status", "uploaded_by", "date")
    search_fields = ("name", "description", "target")
    ordering = ("-date",)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin configuration for Dataset."""

    list_display = ("name", "uploaded_by", "date")
    list_filter = ("uploaded_by", "date")
    search_fields = ("name", "description")
    ordering = ("-date",)


admin.site.unregister(User)
admin.site.unregister(Group)
