#!/bin/bash
set -e

sleep 25

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio worker -l info --scheduler django