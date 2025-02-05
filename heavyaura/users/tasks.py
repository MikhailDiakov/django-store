from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode


@shared_task
def send_reset_email(user_id, domain, protocol):
    User = get_user_model()
    user = User.objects.get(id=user_id)

    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(str(user.pk).encode("utf-8"))

    context = {
        "user": user,
        "site_name": domain,
        "protocol": protocol,
        "domain": domain,
        "uid": uidb64,
        "token": token,
    }

    subject = "Password Reset Request"
    message = render_to_string("users/password_reset_email.html", context)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=message,
    )
