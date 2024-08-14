from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import redis
import threading
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initial Redis instances (not assigned yet)
redis_instances = {
    "main": {},
    "backup": {}
}

# Redis instances configuration
redis_configs = [
    {"host": "localhost", "port": 6379, "db" : 0},
    {"host": "localhost", "port": 6380, "db" : 0}
]

# Function to check Redis connection health
def check_redis_connection(host, port):
    try:
        r = redis.Redis(host=host, port=port)
        r.ping()
        return True
    except redis.ConnectionError:
        return False

# Function to assign Redis instances dynamically
def assign_redis_instances():
    global redis_instances
    healthy_instances = [config for config in redis_configs if check_redis_connection(config['host'], config['port'])]
    
    if len(healthy_instances) == 0:
        print("No healthy Redis instances available.")
    elif len(healthy_instances) == 1:
        redis_instances["main"] = healthy_instances[0]
        redis_instances["backup"] = {}
    else:
        redis_instances["main"] = healthy_instances[0]
        redis_instances["backup"] = healthy_instances[1]

    print(f"Assigned instances: {redis_instances}")  # Debug print

# Function to periodically check and update Redis instances
def periodic_redis_check(interval=60):  # 600 seconds = 10 minutes
    while True:
        assign_redis_instances()
        time.sleep(interval)

# Start the periodic check in a separate thread
threading.Thread(target=periodic_redis_check, daemon=True).start()

@socketio.on('request_redis_address')
def handle_request(data):
    instance_type = data.get('type')
    response_data = redis_instances.get(instance_type, {})
    print(f"Sending address for {instance_type}: {response_data}")  # Debug print
    emit('redis_address', response_data)

if __name__ == '__main__':
    # Initial assignment of Redis instances before starting the server
    assign_redis_instances()
    socketio.run(app, host="127.0.0.1", port=5006, debug=True, allow_unsafe_werkzeug=True)
