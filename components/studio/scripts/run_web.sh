#!/bin/bash

# If we have set a local, custom settings.py, then use that.
#[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings

# To allow setting up fixtures and init DB data for only the first time
if [ -z $INIT ]; then
    INIT=true # if one forgets to pass the init flag, true is assumed so to install fixtures and create the admin 
else
    INIT=$1 # should be either true or false
fi

if

# To enable FEDn in STACKn
if [ -z $FEDN ]; then
    FEDN=false  # if one forgets to pass such flag, false is assumed
else
    FEDN=$2 # should be either true or false
fi

if $INIT; then
    echo "Running studio migrations..."
    python3 manage.py makemigrations
    python3 manage.py migrate

    # NOTE: The following fixtures and super user creation are executed as a helm post-install k8s job, thus disabled here.
    # However for testing and developement purpose, activate them when not using a post-install job

    echo "Loading Studio Fixtures..."
    # Related to Projects (including project meta-resources such as flavours, environments, etc...)
    python3 manage.py loaddata projects/fixtures/projects_templates.json
    #Related to Apps (including celery tasks and intervals)
    python3 manage.py loaddata apps/fixtures/intervals_fixtures.json
    python3 manage.py loaddata apps/fixtures/periodic_tasks_fixtures.json
    python3 manage.py loaddata apps/fixtures/appcats_fixtures.json
    python3 manage.py loaddata apps/fixtures/apps_fixtures.json
    python3 manage.py runscript load_apps_logo -v2
    # Related to Models
    python3 manage.py loaddata models/fixtures/objecttype_fixtures.json

    # HELM deployment: DJANGO_SUPERUSER_PASSWORD should be an env var within the stackn-studio pod
    # python3 manage.py createsuperuser --email $DJANGO_SUPERUSER_EMAIL --username $DJANGO_SUPERUSER --no-input

    # ONLY for local testing with docker-compose
    export DJANGO_SUPERUSER_PASSWORD='dGhpaXNhdmVyeW5vdHNhZmVvbmx'
    python3 manage.py createsuperuser --email 'admin@test.com' --username 'admin' --no-input

    if $FEDN; then
        python3 manage.py runscript load_FEDn -v2
    fi
fi

echo "Starting the Studio server..."
python3 manage.py runserver 0.0.0.0:8080

# Alternative to be used:
# watchmedo auto-restart -R --patterns="*.py" -- daphne studio.asgi:application -b 0.0.0.0 -p 8080
# gunicorn studio.wsgi -b 0.0.0.0:8080 --reload

