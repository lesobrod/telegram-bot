import os
from dotenv import load_dotenv
import redis
from config import DATA_BASE_ENDPOINT

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

REDIS_PASS = os.getenv('REDIS_PASS')

redis_db = redis.StrictRedis(
    host=DATA_BASE_ENDPOINT,
    port=17913,
    password=REDIS_PASS,
    db=0,
    charset='utf-8',
    decode_responses=True
)
