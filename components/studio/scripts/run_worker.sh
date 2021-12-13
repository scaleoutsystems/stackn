#!/bin/bash
set -e

sleep 20

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio worker -l info --scheduler django