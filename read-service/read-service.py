from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
import uuid

class RabbitMQService:
    def __init__(self, host='localhost'):
        self.rabbitmq_host = host

    def send_to_rabbitmq(self, payload):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
        channel = connection.channel()

        # Declare the queue
        channel.queue_declare(queue='read_queue')

        # Send message to the queue
        correlation_id = str(uuid.uuid4())
        response_queue = f'response_queue_{correlation_id}'

        # Declare a unique response queue
        channel.queue_declare(queue=response_queue)

        channel.basic_publish(
            exchange='',
            routing_key='read_queue',
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                reply_to=response_queue,
                correlation_id=correlation_id
            )
        )

        connection.close()
        return correlation_id, response_queue

    def receive_from_rabbitmq(self, correlation_id, response_queue):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
        channel = connection.channel()

        # Declare the response queue
        channel.queue_declare(queue=response_queue)

        response = {}

        def on_response(ch, method, properties, body):
            if properties.correlation_id == correlation_id:
                nonlocal response
                response = json.loads(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()

        channel.basic_consume(queue=response_queue, on_message_callback=on_response)
        channel.start_consuming()

        # Cleanup the response queue after consumption
        channel.queue_delete(queue=response_queue)
        connection.close()
        return response


class ReadService:
    def __init__(self, rabbitmq_service):
        self.rabbitmq_service = rabbitmq_service

    def handle_read_request(self, data):
        collection = data.get('collection')
        document = data.get('document')
        field = data.get('field')

        # Prepare the request payload
        payload = {
            'collection': collection,
            'document': document,
            'field': field
        }

        # Send to RabbitMQ and receive response
        correlation_id, response_queue = self.rabbitmq_service.send_to_rabbitmq(payload)
        result = self.rabbitmq_service.receive_from_rabbitmq(correlation_id, response_queue)

        # Handle the result
        if "error" in result:
            return jsonify(result), 404

        return jsonify(result), 200


class ReadApp:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.rabbitmq_service = RabbitMQService()
        self.read_service = ReadService(self.rabbitmq_service)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/read', methods=['POST'])
        def read_structure():
            data = request.json
            return self.read_service.handle_read_request(data)

    def run(self):
        self.app.run(port=5001, host="127.0.0.1", debug=True)


if __name__ == '__main__':
    app = ReadApp()
    app.run()
