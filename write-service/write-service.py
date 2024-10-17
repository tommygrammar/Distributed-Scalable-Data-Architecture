from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
import requests

class RabbitMQService:
    def __init__(self, host='localhost'):
        self.rabbitmq_host = host

    def send_data_to_rabbitmq(self, data):
        connection = pika.BlockingConnection(pika.ConnectionParameters(self.rabbitmq_host))
        channel = connection.channel()

        # Declare the queue as durable
        channel.queue_declare(queue='write_queue', durable=True)

        # Publish the message to the queue with persistence
        channel.basic_publish(
            exchange='',
            routing_key='write_queue',
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            )
        )
        connection.close()
        return "success"


class WriteService:
    def __init__(self, rabbitmq_service):
        self.rabbitmq_service = rabbitmq_service

    def handle_write_request(self, data):
        collection = data.get('collection')
        document = data.get('document')
        fields = data.get('fields', {})

        # Validate required fields
        if not collection or not document or not fields:
            return jsonify({"error": "Main collection, document, and fields are required."}), 400

        # Prepare the data to send to RabbitMQ
        payload = {
            'collection': collection,
            'document': document,
            'fields': fields
        }

        # Send the data to RabbitMQ for queuing
        response = self.rabbitmq_service.send_data_to_rabbitmq(payload)

        # Prepare the message for the publish endpoint
        message = {'collection': collection, 'document': document, **fields}
        requests.post('http://localhost:5005/publish', json=message)

        # Check the response and return appropriate message
        if response == "success":
            return jsonify({"message": "Data successfully queued for writing."}), 200
        else:
            return jsonify({"error": "Failed to queue data."}), 500


# Initialize Flask app, CORS, and services
app = Flask(__name__)
CORS(app)
rabbitmq_service = RabbitMQService(host='localhost')
write_service = WriteService(rabbitmq_service=rabbitmq_service)

# Define the write route
@app.route('/write', methods=['POST'])
def write_structure():
    data = request.json
    return write_service.handle_write_request(data)


if __name__ == '__main__':
    app.run(port=5002, host="127.0.0.1", debug=True)
