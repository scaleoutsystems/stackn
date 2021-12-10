#!/bin/bash
set -e

sleep 15

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler