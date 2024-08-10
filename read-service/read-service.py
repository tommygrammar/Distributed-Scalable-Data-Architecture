from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
import uuid
import requests

app = Flask(__name__)
CORS(app)

rabbitmq_host = 'localhost'

def send_to_rabbitmq(payload):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue='read_queue')

    # Send message to the queue
    correlation_id = str(uuid.uuid4())
    response_queue = 'response_queue_' + correlation_id

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

def receive_from_rabbitmq(correlation_id, response_queue):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
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

##receives read  request
@app.route('/read', methods=['POST'])
def read_structure():
    
    data = request.json
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
    correlation_id, response_queue = send_to_rabbitmq(payload)
    result = receive_from_rabbitmq(correlation_id, response_queue)

    # Handle the result
    if "error" in result:
        return jsonify(result), 404

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(port=5001, host="127.0.0.1", debug=True)
