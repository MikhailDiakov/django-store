from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from main.models import Product
from .cart import Cart
from .forms import CartAddProduct
from main.logs_service import log_to_kafka


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProduct(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        log_to_kafka(
            "Product added to cart",
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": cd["quantity"],
                "user": (
                    request.user.username if request.user.is_authenticated else "guest"
                ),
            },
        )
        cart.add(
            product=product, quantity=cd["quantity"], override_quantity=cd["override"]
        )
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    log_to_kafka(
        "Product removed from cart",
        {
            "product_id": product.id,
            "product_name": product.name,
            "user": request.user.username if request.user.is_authenticated else "guest",
        },
    )
    cart.remove(product)
    return redirect("cart:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart})
