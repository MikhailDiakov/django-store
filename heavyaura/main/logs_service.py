from kafka import KafkaProducer
import json


def log_to_kafka(message, extra_data=None):
    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    log_data = {
        "message": message,
        "extra_data": extra_data,
    }

    producer.send("logs", log_data)
    producer.flush()
