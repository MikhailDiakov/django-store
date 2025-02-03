import json
import random
import string
from decimal import Decimal, ROUND_DOWN
from django.conf import settings
import redis
from main.models import Product
from datetime import timedelta
from .tasks import clear_cart


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.redis_client = redis.StrictRedis.from_url(
            settings.CACHES["default"]["LOCATION"]
        )
        if request.user.is_authenticated:
            self.cart_key = f"cart_{request.user.id}"
            self.cart_ttl = timedelta(days=7)
        else:
            if "cart_token" not in self.session:
                self.session["cart_token"] = "".join(
                    random.choices(string.ascii_letters + string.digits, k=16)
                )
            self.cart_key = f"cart_{self.session['cart_token']}"
            self.cart_ttl = timedelta(minutes=30)

        self.cart = self.redis_client.get(self.cart_key)
        if not self.cart:
            self.cart = {}
        else:
            self.cart = json.loads(self.cart)

        self.redis_client.expire(self.cart_key, self.cart_ttl)

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}
        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def save(self):
        self.redis_client.set(self.cart_key, json.dumps(self.cart))
        self.redis_client.expire(self.cart_key, self.cart_ttl)

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]["product"] = product
        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = (item["price"] * item["quantity"]).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )

            product = item.get("product")
            discount_percentage = (
                Decimal(product.discount)
                if product and hasattr(product, "discount")
                else Decimal(0)
            )

            item["discount"] = discount_percentage

            item["discounted_price"] = (
                item["price"] * (1 - discount_percentage / 100)
            ) * item["quantity"]
            item["discounted_price"] = item["discounted_price"].quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )

            yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def clear(self):
        clear_cart.apply_async((self.cart_key,))

    def get_total_price(self):
        total = sum(
            (
                Decimal(item["price"])
                - (Decimal(item["price"]) * Decimal(item["product"].discount / 100))
            )
            * item["quantity"]
            for item in self.cart.values()
        )
        return format(total, ".2f")
