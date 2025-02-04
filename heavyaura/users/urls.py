from django.urls import path
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from . import views


app_name = "users"

urlpatterns = [
    path("login/", views.login, name="login"),
    path("registration/", views.registration, name="registration"),
    path("profile/", views.profile, name="profile"),
    path("logout/", views.logout, name="logout"),
    path(
        "password-change/", views.UserPasswordChange.as_view(), name="password-change"
    ),
    path(
        "password-change/done",
        PasswordChangeDoneView.as_view(template_name="users/password_change_done.html"),
        name="password_change_done",
    ),
]
