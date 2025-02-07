import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe.error
from orders.models import Order
from .tasks import process_payment_status
from main.logs_service import log_to_kafka


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        log_to_kafka("Invalid payload", {"error": str(e)})
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        log_to_kafka("Invalid signature", {"error": str(e)})
        return HttpResponse(status=400)

    if event.type == "checkout.session.completed":
        session = event.data.object
        if session.mode == "payment" and session.payment_status == "paid":
            try:
                order = Order.objects.get(id=session.client_reference_id)
                log_to_kafka("Order found", {"order_id": order.id})
            except Order.DoesNotExist:
                log_to_kafka(
                    "Order not found", {"order_id": session.client_reference_id}
                )
                return HttpResponse(status=404)

            process_payment_status.apply_async((order.id, session.payment_intent))
            log_to_kafka(
                "Payment processed",
                {"order_id": order.id, "payment_intent": session.payment_intent},
            )

    return HttpResponse(status=200)
