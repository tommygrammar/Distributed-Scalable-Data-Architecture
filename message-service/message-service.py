from flask import Flask, request, jsonify
import pika
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# RabbitMQ connection
def connect_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='database_updates')
    return connection, channel

connection, channel = connect_rabbitmq()

def publish_message(channel, message):
    try:
        channel.basic_publish(exchange='', routing_key='database_updates', body=json.dumps(message))
    except pika.exceptions.ChannelWrongStateError:
        global connection
        connection, channel = connect_rabbitmq()
        channel.basic_publish(exchange='', routing_key='database_updates', body=json.dumps(message))
    return channel

@app.route('/publish', methods=['POST'])
def publish():
    message = request.json
    global channel
    channel = publish_message(channel, message)
    return jsonify({"message": "Message published"}), 200

def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message: {message}")
    # Process the message as needed

@app.route('/subscribe', methods=['GET'])
def subscribe():
    connection, channel = connect_rabbitmq()
    channel.basic_consume(queue='database_updates', on_message_callback=callback, auto_ack=True)
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    return jsonify({"message": "Subscribed to messages"}), 200

if __name__ == '__main__':
    app.run(port=5005, host = "127.0.0.1", debug=True)
