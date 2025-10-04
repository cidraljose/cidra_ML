from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render


def home(request):
    context = {}
    if not request.user.is_authenticated:
        login_form = AuthenticationForm()
        register_form = UserCreationForm()
        context = {"login_form": login_form, "register_form": register_form}
    return render(request, "home.html", context)


def about(request):
    return render(request, "about.html")
