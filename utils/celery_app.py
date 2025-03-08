from celery import Celery
import os
import logging
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger('celery')
logger.setLevel(logging.INFO)

fh = logging.FileHandler('celery.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('\033[1;36m%(asctime)s\033[0m [%(levelname)s] %(message)s')

fh.setFormatter(file_formatter)
ch.setFormatter(console_formatter)

logger.addHandler(fh)
logger.addHandler(ch)

logger.propagate = True


REDIS_HOST = "119.59.99.192"
REDIS_PORT = 6379
REDIS_DB = 0

try:
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    redis_client.ping()
    logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except RedisError as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    raise

redis_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
# Add this near the top of the file, after imports
celery_app = Celery('face_detection',
                    broker=redis_url,
                    backend=redis_url,
                    include=['Upload_images.router'])  # Add this line

celery_app.conf.update(
    broker_connection_retry_on_startup=True,  # Add this line
    task_serializer='pickle',
    accept_content=['pickle', 'json'],
    result_serializer='pickle',
    task_track_started=True,
    task_time_limit=300,
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_redirect_stdouts=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
)

# Optional configurations
celery_app.conf.update(
    task_serializer='pickle',
    accept_content=['pickle', 'json'],  # Allows pickle for numpy array serialization
    result_serializer='pickle',
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
    task_ignore_result=False,  # Enable task results
    task_store_errors_even_if_ignored=True,  # Store errors even if results are ignored
    worker_redirect_stdouts=False,  # Prevent Celery from capturing stdout/stderr
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
)