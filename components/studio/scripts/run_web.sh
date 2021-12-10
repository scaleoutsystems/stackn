#!/bin/bash
set -e

# If we have set a local, custom settings.py, then use that.
#[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings

# echo "Running studio migrations..."
python3 manage.py makemigrations
python3 manage.py migrate

# NOTE: The following fixtures and super user creation are executed as a helm post-install k8s job, thus disabled here.
# However for testing and developement purpose, activate them when not using a post-install job

echo "Loading Studio Fixtures..."
# # Related to Projects (including project meta-resources such as flavours, environments, etc...)
python3 manage.py loaddata projects/fixtures/projects_templates.json
# # Related to Apps (including celery tasks and intervals)
python3 manage.py loaddata apps/fixtures/intervals_fixtures.json
python3 manage.py loaddata apps/fixtures/periodic_tasks_fixtures.json
python3 manage.py loaddata apps/fixtures/appcats_fixtures.json
python3 manage.py loaddata apps/fixtures/apps_fixtures.json

# HELM deployment: DJANGO_SUPERUSER_PASSWORD should be an env var within the stackn-studio pod
# python3 manage.py createsuperuser --email $DJANGO_SUPERUSER_EMAIL --username $DJANGO_SUPERUSER --no-input

# ONLY for local testing with docker-compose!!!
export DJANGO_SUPERUSER_PASSWORD = 'dGhpaXNhdmVyeW5vdHNhZmVvbmx'
python3 manage.py createsuperuser --email 'admin@test.com' --username 'admin' --no-input

echo "Starting the Studio server..."
python3 manage.py runserver 0.0.0.0:8080

# Alternative to be used:
# watchmedo auto-restart -R --patterns="*.py" -- daphne studio.asgi:application -b 0.0.0.0 -p 8080
# gunicorn studio.wsgi -b 0.0.0.0:8080 --reload

