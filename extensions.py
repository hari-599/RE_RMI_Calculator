from flask_mail import Mail
import os
import redis
mail = Mail()


redis_url = os.getenv('REDIS_URL', 'redis://default:AcasAAIjcDFjMzIyMGRhMDY5NDA0NGU5ODE5ZGYxNTBlY2JhM2ZlZXAxMA@fancy-mouse-50860.upstash.io:6379')

redis_client = redis.from_url(redis_url, decode_responses=True, ssl=True)