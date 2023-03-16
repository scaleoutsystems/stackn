#!/bin/bash
set -e

# Giving time to studio container to run DB migrations
sleep 25

if $DEBUG ; then
    watchmedo auto-restart -R --patterns="*.py" -- celery -A studio worker -l info --scheduler django
else
    celery -A studio worker -l info --scheduler django
fi