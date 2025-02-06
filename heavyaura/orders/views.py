from django.shortcuts import render, redirect
from django.urls import reverse
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from main.logs_service import log_to_kafka


def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST, request=request)
        if form.is_valid():
            order = form.save()
            log_to_kafka(
                "Order created",
                {
                    "order_id": order.id,
                    "user": (
                        request.user.username
                        if request.user.is_authenticated
                        else "guest"
                    ),
                },
            )
            for item in cart:
                discounted_price = item["product"].sell_price()
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=discounted_price,
                    quantity=item["quantity"],
                )
                log_to_kafka(
                    "Item added to order",
                    {
                        "order_id": order.id,
                        "product_id": item["product"].id,
                        "product_name": item["product"].name,
                        "quantity": item["quantity"],
                        "price": str(discounted_price),
                    },
                )
            cart.clear()
            request.session["order_id"] = order.id
            log_to_kafka(
                "Cart cleared",
                {
                    "order_id": order.id,
                    "user": (
                        request.user.username
                        if request.user.is_authenticated
                        else "guest"
                    ),
                },
            )
            return redirect(reverse("payment:process"))
        else:
            log_to_kafka(
                "Order creation failed",
                {
                    "errors": form.errors,
                    "user": (
                        request.user.username
                        if request.user.is_authenticated
                        else "guest"
                    ),
                },
            )
    else:
        form = OrderCreateForm(request=request)
        return render(request, "order/create.html", {"cart": cart, "form": form})
