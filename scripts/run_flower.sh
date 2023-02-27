#!/bin/bash
set -e

#Script currently only used in helm chart deployment

# Giving time to studio container to run DB migrations
sleep 25

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio --broker=amqp://$RABBITMQ_USER:$RABBITMQ_DEFAULT_PASS@$RABBITMQ_HOST:5672// --result-backend redis://$REDIS_HOST:6379/0 flower --port=5556 --broker_api=http://$RABBITMQ_USER:$RABBITMQ_DEFAULT_PASS@$RABBITMQ_HOST:15672/api//