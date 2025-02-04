from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "user",
            "first_name",
            "last_name",
            "email",
            "city",
            "address",
            "postal_code",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            self.initial["first_name"] = self.request.user.first_name
            self.initial["last_name"] = self.request.user.last_name
            self.initial["email"] = self.request.user.email
            latest_order = Order.objects.filter(user=user).order_by("-created").first()
            if latest_order:
                self.initial["city"] = latest_order.city
                self.initial["address"] = latest_order.address
                self.initial["postal_code"] = latest_order.postal_code

    def save(self, commit=True):
        order = super().save(commit=False)
        if self.request.user.is_authenticated:
            order.user = self.request.user
        else:
            order.user = None
        if commit:
            order.save()
        return order
