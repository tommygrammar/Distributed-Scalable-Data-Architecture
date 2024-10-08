import redis
import json
import pika
import socketio
import threading
import time

class WriteDistributionService:
    def __init__(self, mds_host='localhost', mds_port=5006, refresh_interval=60):
        self.sio = socketio.Client()
        self.mds_host = mds_host
        self.mds_port = mds_port
        self.refresh_interval = refresh_interval

        self.redis_addresses = self.get_redis_addresses(mds_host, mds_port)
        self.redis_client1 = redis.Redis(host=self.redis_addresses['main']['host'], port=self.redis_addresses['main']['port'], db=0)
        self.redis_client2 = redis.Redis(host=self.redis_addresses['backup']['host'], port=self.redis_addresses['backup']['port'], db=0)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='write_queue', durable=True)

        # Start a background thread to periodically refresh the Redis addresses
        self.refresh_thread = threading.Thread(target=self.periodic_redis_refresh, daemon=True)
        self.refresh_thread.start()

    def get_redis_addresses(self, mds_host, mds_port):
        self.sio.connect(f"http://{mds_host}:{mds_port}")
        addresses = {}

        @self.sio.on('redis_address')
        def handle_redis_address(data):
            if 'host' in data and 'port' in data:
                if 'main' not in addresses:
                    addresses['main'] = data
                else:
                    addresses['backup'] = data

        # Request main Redis address
        self.sio.emit('request_redis_address', {'type': 'main'})
        self.sio.sleep(1)  # Adjust the sleep time as necessary
        
        # Request backup Redis address
        self.sio.emit('request_redis_address', {'type': 'backup'})
        self.sio.sleep(1)  # Adjust the sleep time as necessary
        
        self.sio.disconnect()

        if not addresses.get('main') or not addresses.get('backup'):
            raise Exception("Failed to retrieve Redis addresses from MDS")

        return addresses

    def refresh_redis_clients(self):
        # Get the latest Redis addresses
        new_redis_addresses = self.get_redis_addresses(self.mds_host, self.mds_port)
        if new_redis_addresses != self.redis_addresses:
            print(f"Updating Redis addresses from {self.redis_addresses} to {new_redis_addresses}")
            self.redis_addresses = new_redis_addresses
            self.redis_client1 = redis.Redis(host=self.redis_addresses['main']['host'], port=self.redis_addresses['main']['port'], db=0)
            self.redis_client2 = redis.Redis(host=self.redis_addresses['backup']['host'], port=self.redis_addresses['backup']['port'], db=0)

    def periodic_redis_refresh(self):
        while True:
            self.refresh_redis_clients()
            time.sleep(self.refresh_interval)

    def write_data(self, collection, document, fields):
        try:
            for field, content in fields.items():
                if content is not None:
                    self.redis_client1.hset(f"{collection}:{document}", field, content)
                    self.redis_client2.hset(f"{collection}:{document}", field, content)
            return "success"
        except Exception as e:
            print(f"Error writing to Redis: {e}")
            return "error"

    def callback(self, ch, method, properties, body):
        data = json.loads(body)
        collection = data.get('collection')
        document = data.get('document')
        fields = data.get('fields')

        response = self.write_data(collection, document, fields)

        if response == "success":
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print("Failed to write data to Redis")

    def consume_queue(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='write_queue', on_message_callback=self.callback)
        print('Waiting for messages...')
        self.channel.start_consuming()

if __name__ == "__main__":
    wds = WriteDistributionService()
    wds.consume_queue()
