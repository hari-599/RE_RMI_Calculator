from flask_mail import Mail
import os
import redis
mail = Mail()

redis_url = os.getenv('REDIS_URL')
if redis_url:
    # Use rediss:// for SSL, do NOT pass ssl=True
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
    redis_client = redis.StrictRedis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )