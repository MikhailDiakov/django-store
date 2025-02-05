from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from .forms import (
    UserLoginForm,
    UserRegistrationForm,
    ProfileForm,
    UserPasswordChangeForm,
)
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from orders.models import Order, OrderItem
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.contrib.auth import get_user_model
from .tasks import send_reset_email
from django.core.exceptions import ObjectDoesNotExist


def login(request):
    if request.method == "POST":
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST["username"]
            password = request.POST["password"]
            user = auth.authenticate(username=username, password=password)

            if user:
                auth.login(request, user)
                return HttpResponseRedirect(reverse("main:product_list"))
            else:
                messages.error(request, "Invalid username or password")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserLoginForm()
    return render(request, "users/login.html", {"form": form})


def registration(request):
    if request.method == "POST":
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = form.instance
            auth.login(request, user)
            messages.success(request, f"{user.username}, Successful Registration")
            return HttpResponseRedirect(reverse("user:login"))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")

    else:
        form = UserRegistrationForm()

    return render(request, "users/registration.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(
            data=request.POST, instance=request.user, files=request.FILES
        )
        if form.is_valid():
            form.save()
            messages.success(request, " Profile was changed ")
            return HttpResponseRedirect(reverse("user:profile"))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ProfileForm(instance=request.user)

    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        )
        .order_by("-id")
    )
    return render(request, "users/profile.html", {"form": form, "orders": orders})


def logout(request):
    auth.logout(request)
    return redirect(reverse("main:product_list"))


class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):

        email = form.cleaned_data["email"]
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(self.get_success_url())

        protocol = "https" if self.request.is_secure() else "http"
        domain = self.request.get_host()

        send_reset_email.delay(user.id, domain, protocol)
        return HttpResponseRedirect(self.get_success_url())
