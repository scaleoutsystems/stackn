#!/usr/bin/env bash

# wait for RabbitMQ server to start
sleep 10

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
#su -m myuser -c "celery worker -A myproject.celeryconf -Q default -n default@%h"
su -m worker -c "celery worker -A registrar.celery -Q celery,orchestrator -l info" # -Q default -n default@%h -l debug"