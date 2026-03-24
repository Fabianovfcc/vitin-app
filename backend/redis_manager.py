import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

class RedisManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
        return cls._instance

    def publish_notification(self, channel, message_data):
        """Publica uma notificação em um canal específico."""
        self.client.publish(channel, json.dumps(message_data))

    def set_active_user(self, user_id):
        """Marca um usuário como online."""
        self.client.setex(f"user:active:{user_id}", 300, "online")

    def is_user_online(self, user_id):
        """Verifica se o usuário está online."""
        return self.client.exists(f"user:active:{user_id}")

redis_manager = RedisManager()
