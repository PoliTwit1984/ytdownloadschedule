import multiprocessing
import os

workers = multiprocessing.cpu_count() * 2 + 1
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

timeout = 600  # 10 minutes
keepalive = 5
max_requests = 1000
worker_class = 'sync'

# Logging
accesslog = '-'
errorlog = '-'