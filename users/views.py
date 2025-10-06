from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("home_view")
    # For a GET request or failed login, redirect back to home
    messages.error(request, "Invalid username or password.")
    return redirect("home_view")


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("home_view")
        else:
            # If form is invalid, render home page with the form and errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    return redirect("home_view")


def logout_view(request):
    """Logs the user out and renders the home page."""
    auth_logout(request)
    messages.success(request, "You have been successfully logged out.")
    login_form = AuthenticationForm()
    register_form = UserCreationForm()
    return render(
        request, "home.html", {"login_form": login_form, "register_form": register_form}
    )
