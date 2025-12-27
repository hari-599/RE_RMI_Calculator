from flask_mail import Mail
mail = Mail()
import os
import logging
import redis
import fakeredis

redis_url = os.getenv('REDIS_URL')
use_fake = os.getenv('USE_FAKE_REDIS')

# Default: try real Redis with short timeouts; if it fails, fall back to fakeredis for debugging
if use_fake:
    try:
        redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    except Exception:
        logging.exception('fakeredis import failed; redis_client set to None')
        redis_client = None
else:
    try:
        if redis_url:
            # from_url supports rediss://; add short timeouts so a bad host fails fast
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                ssl_cert_reqs=None,
            )
        else:
            redis_client = redis.StrictRedis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

        # verify quickly; if ping raises, we will fall back
        try:
            redis_client.ping()
        except Exception:
            raise
    except Exception:
        logging.exception('Redis connection failed; falling back to fakeredis for debugging.')
        try:
            redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
        except Exception:
            logging.exception('fakeredis import failed; redis_client set to None')
            redis_client = None