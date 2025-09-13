from django.urls import path

from home.views import about, home  # , contact

urlpatterns = [
    path("", home, name="home_view"),
    path("about/", about, name="about_view"),
    # path("contact/", contact),
]
