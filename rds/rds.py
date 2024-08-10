import redis
import json
import pika
import socketio


class RedisService:
    def __init__(self, mds_host='localhost', mds_port=5006):
        self.sio = socketio.Client()
        self.redis_address = self.get_redis_address(mds_host, mds_port)
        if not self.redis_address:
            raise Exception("Failed to retrieve Redis address from MDS")
        self.redis_client = redis.Redis(host=self.redis_address['host'], port=self.redis_address['port'], db=0)
        self.rabbitmq_host = 'localhost'

    def get_redis_address(self, mds_host, mds_port):
        # Connect to MDS
        self.sio.connect(f"http://{mds_host}:{mds_port}")

        redis_address = {}

        # Event handler to receive Redis address
        @self.sio.on('redis_address')
        def handle_response(data):
            nonlocal redis_address
            redis_address = data

        # Emit request for Redis address
        self.sio.emit('request_redis_address', {'type': 'backup'})
        
        # Allow some time for the response
        self.sio.sleep(1)
        
        # Disconnect after receiving the address
        self.sio.disconnect()

        return redis_address

    def get_data(self, collection=None, document=None, field=None):
        result = {}
        pattern = f"{collection}:*" if collection else "*"
        keys = self.redis_client.keys(pattern)

        if not keys:
            return {"error": f"Collection '{collection}' does not exist."}

        for key in keys:
            key_str = key.decode('utf-8')
            key_type = self.redis_client.type(key).decode('utf-8')

            if key_type == 'hash':
                key_parts = key_str.split(':')
                if len(key_parts) < 2:
                    continue

                collection_name = key_parts[0]
                doc_name = key_parts[1]

                if document and document != doc_name:
                    continue

                if collection and collection_name != collection:
                    continue

                if collection_name not in result:
                    result[collection_name] = {}
                if doc_name not in result[collection_name]:
                    result[collection_name][doc_name] = {}

                fields = self.redis_client.hgetall(key)
                fields = {k.decode('utf-8'): v.decode('utf-8') for k, v in fields.items()}

                if field:
                    if field in fields:
                        result[collection_name][doc_name] = {field: fields[field]}
                    else:
                        return {"error": f"Field '{field}' does not exist in document '{doc_name}'."}
                else:
                    result[collection_name][doc_name] = fields
            else:
                print(f"Skipping key {key_str} of type {key_type}")
                
        return result

    def on_request(self, ch, method, props, body):
        request_data = json.loads(body)
        collection = request_data.get('collection')
        document = request_data.get('document')
        field = request_data.get('field')

        response_data = self.get_data(collection=collection, document=document, field=field)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps(response_data)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    def start_service(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
        channel = connection.channel()

        channel.queue_declare(queue='read_queue')

        channel.basic_consume(queue='read_queue', on_message_callback=self.on_request)

        print(" [x] Awaiting RPC requests")
        channel.start_consuming()

if __name__ == "__main__":
    rds = RedisService()
    rds.start_service()
