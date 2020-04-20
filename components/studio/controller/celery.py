from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
#TODO import settings module
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'registrar.settings')

app = Celery('registrar',
             result_backend='redis://redis:6379/0')  # , broker='amqp://admin:sp3ctr4l@rabbit:5672//?heartbeat=30')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# app.config_from_object('registrar.settings', namespace='CELERY')

"""
from kombu.common import Broadcast

app.conf.task_queues = (Broadcast('broadcast_tasks'),)
app.conf.task_routes = {
    'tasks.reload_cache': {
        'queue': 'broadcast_tasks',
        'exchange': 'broadcast_tasks'
    }
}"""
from kombu import Exchange, Queue
from celery.exceptions import Reject

default_queue_name = 'default'
default_exchange_name = 'default'
default_routing_key = 'default'

workers_queue_name = 'workers'
workers_routing_key = 'workers'

orchestrator_queue_name = 'orchestrator'
orchestrator_routing_key = 'orchestrator'
default_exchange = Exchange(default_exchange_name, type='direct')
default_queue = Queue(
    default_queue_name,
    default_exchange,
    routing_key=default_routing_key)

workers_queue = Queue(
    workers_queue_name,
    default_exchange,
    routing_key=workers_routing_key)

orchestrator_queue = Queue(
    orchestrator_queue_name,
    default_exchange,
    routing_key=orchestrator_queue_name)

app.conf.task_queues = (default_queue, workers_queue, orchestrator_queue)

app.conf.task_default_queue = default_queue_name
app.conf.task_default_exchange = default_exchange_name
app.conf.task_default_routing_key = default_routing_key

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
