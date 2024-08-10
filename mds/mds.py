from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# IPs and Ports for main and backup Redis instances
redis_instances = {
    "main": {"host": "localhost", "port": 6379},
    "backup": {"host": "localhost", "port": 6380}
}

@socketio.on('request_redis_address')
def handle_request(data):
    instance_type = data.get('type')
    response_data = redis_instances.get(instance_type, {})
    print(f"Sending address for {instance_type}: {response_data}")  # Debug print
    emit('redis_address', response_data)

if __name__ == '__main__':
    socketio.run(app, host = "127.0.0.1", port=5006, debug=True, allow_unsafe_werkzeug=True)

