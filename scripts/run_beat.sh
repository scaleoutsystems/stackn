#!/bin/bash
set -e

# Giving time to studio container to run DB migrations
sleep 25

if $DEBUG ; then
    watchmedo auto-restart -R --patterns="*.py" -- celery -A studio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    celery -A studio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
fi