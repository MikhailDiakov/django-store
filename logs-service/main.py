import time
import json
from kafka import KafkaConsumer
import os
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import uuid
from datetime import datetime


def get_cassandra_session():
    cluster = None
    session = None
    while not session:
        try:
            cluster = Cluster([os.environ["CASSANDRA_HOST"]], port=9042)
            session = cluster.connect()
        except Exception as e:
            time.sleep(5)
    return session


def create_log_table(session):
    create_keyspace(session)
    session.set_keyspace("logs")


def create_keyspace(session):
    keyspace_query = """
    CREATE KEYSPACE IF NOT EXISTS logs
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """
    session.execute(keyspace_query)
    session.set_keyspace("logs")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS log_entries (
        id UUID PRIMARY KEY,
        message TEXT,
        extra_data TEXT,
        timestamp TIMESTAMP
    );
    """
    session.execute(create_table_query)


def save_log_to_cassandra(session, message, extra_data=None):
    log_id = uuid.uuid4()
    timestamp = datetime.utcnow()

    extra_data_str = json.dumps(extra_data) if extra_data else None

    query = SimpleStatement(
        """
        INSERT INTO log_entries (id, message, extra_data, timestamp)
        VALUES (%s, %s, %s, %s)
    """
    )

    session.execute(query, (log_id, message, extra_data_str, timestamp))


def create_consumer():
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                "logs", bootstrap_servers=os.environ["KAFKA_BROKER"]
            )
        except Exception as e:
            time.sleep(5)
    return consumer


consumer = create_consumer()

session = get_cassandra_session()
create_keyspace(session)

for message in consumer:
    log_message = message.value.decode()
    log_data = json.loads(log_message)

    message_content = log_data.get("message")
    extra_data = log_data.get("extra_data")

    save_log_to_cassandra(session, message_content, extra_data)
