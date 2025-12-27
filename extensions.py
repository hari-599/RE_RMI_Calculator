from flask_mail import Mail
mail = Mail()
import os
import redis

redis_url = os.getenv('REDIS_URL')

if redis_url:
    # Adding ssl_cert_reqs=None is the key fix for the "hanging" connection
    redis_client = redis.from_url(
        redis_url, 
        decode_responses=True,
        ssl_cert_reqs=None
    )
else:
    # Local fallback (usually no SSL needed for localhost)
    redis_client = redis.StrictRedis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )