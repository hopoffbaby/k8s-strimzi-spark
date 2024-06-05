from flask import Flask, request, jsonify
from confluent_kafka import Producer
import json

app = Flask(__name__)

AUTH_TOKEN = '9f6d4e30a7d3e4a9b10c8d34d5f3a234'  # Replace with your generated token
KAFKA_TOPIC = 'it-dev-performance-testing'  # Define your Kafka topic name

# Initialize Kafka producer
producer = Producer({'bootstrap.servers': 'data-platform-kafka-kafka-external-bootstrap.it-prod-kafka.k8s.barf1.com:9094'})

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

@app.route('/webhook', methods=['POST'])
def webhook():
    auth_token = request.headers.get('Authorization')
    if auth_token != AUTH_TOKEN:
        return jsonify({'status': 'unauthorized'}), 401

    data = request.json
    print(data)  # Log the received data for auditing

    # Send the event data to Kafka
    producer.produce(KAFKA_TOPIC, key=str(data.get('event', '')), value=json.dumps(data), callback=delivery_report)
    producer.flush()

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
