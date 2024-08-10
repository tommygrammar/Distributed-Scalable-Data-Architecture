from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
import requests

app = Flask(__name__)
CORS(app)

def send_data_to_rabbitmq(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue='write_queue', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='write_queue',
        body=json.dumps(data),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make the message persistent
        ))
    connection.close()
    return "success"

@app.route('/write', methods=['POST'])
def write_structure():

    data = request.json
    collection = data.get('collection')
    document = data.get('document')
    fields = data.get('fields', {})

    if not collection or not document or not fields:
        return jsonify({"error": "Main collection, document, and fields are required."}), 400

    # Prepare the data to send to RabbitMQ
    payload = {
        'collection': collection,
        'document': document,
        'fields': fields
    }

    # Send the data to RabbitMQ for queuing
    response = send_data_to_rabbitmq(payload)

    message = {'collection': collection, 'document': document, **fields}
    requests.post('http://localhost:5005/publish', json=message)

    if response == "success":
        return jsonify({"message": "Data successfully queued for writing."}), 200
    else:
        return jsonify({"error": "Failed to queue data."}), 500

if __name__ == '__main__':
    app.run(port=5002, host="127.0.0.1", debug=True)
