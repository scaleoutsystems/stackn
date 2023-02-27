#!/bin/bash
set -e

# Giving time to studio container to run DB migrations
sleep 25

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio worker -l info --scheduler django