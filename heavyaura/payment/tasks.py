# tasks.py
from celery import shared_task
from orders.models import Order
import stripe
from django.conf import settings
from main.logs_service import log_to_kafka


@shared_task
def process_payment_status(order_id, stripe_payment_intent):
    try:
        order = Order.objects.get(id=order_id)
        order.paid = True
        order.stripe_id = stripe_payment_intent
        order.save()

        log_to_kafka(
            "Payment status updated",
            {
                "order_id": order_id,
                "stripe_payment_intent": stripe_payment_intent,
                "status": "paid",
            },
        )

        return f"Order {order_id} successfully updated with payment status."
    except Order.DoesNotExist:
        log_to_kafka("Order not found", {"order_id": order_id})
        return f"Order with ID {order_id} not found."
