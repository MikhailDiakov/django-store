# tasks.py
from celery import shared_task
from orders.models import Order
import stripe
from django.conf import settings


@shared_task
def process_payment_status(order_id, stripe_payment_intent):
    try:
        order = Order.objects.get(id=order_id)
        order.paid = True
        order.stripe_id = stripe_payment_intent
        order.save()
        return f"Order {order_id} successfully updated with payment status."
    except Order.DoesNotExist:
        return f"Order with ID {order_id} not found."
