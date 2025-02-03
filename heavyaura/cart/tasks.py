from celery import shared_task
import redis
from django.conf import settings


@shared_task
def clear_cart(cart_key):
    redis_client = redis.StrictRedis.from_url(settings.CACHES["default"]["LOCATION"])
    redis_client.delete(cart_key)
    return f"Cart with key {cart_key} has been cleared."
