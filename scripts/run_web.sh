#!/bin/bash

# If we have set a local, custom settings.py, then use that.
#[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings

# To allow setting up fixtures and init DB data for only the first time
if $INIT; then
    echo "Running studio migrations..."
    
    
    python manage.py makemigrations
    python manage.py migrate

    #Replace storageclass in project template fixture
    sed -i "s/microk8s-hostpath/$STUDIO_STORAGECLASS/g" ./fixtures/projects_templates.json

    #Replace accessmode
    sed -i "s/ReadWriteMany/$STUDIO_ACCESSMODE/g" ./fixtures/projects_templates.json
    sed -i "s/ReadWriteMany/$STUDIO_ACCESSMODE/g" ./fixtures/apps_fixtures.json

    # NOTE: The following fixtures and super user creation are executed as a helm post-install k8s job, thus disabled here.
    # However for testing and developement purpose, activate them when not using a post-install job

    echo "Loading Studio Fixtures..."
    # Related to Projects (including project meta-resources such as flavours, environments, etc...)
    python manage.py loaddata fixtures/projects_templates.json
    #Related to Apps (including celery tasks and intervals)
    python manage.py loaddata fixtures/intervals_fixtures.json
    python manage.py loaddata fixtures/periodic_tasks_fixtures.json
    python manage.py loaddata fixtures/appcats_fixtures.json
    python manage.py loaddata fixtures/apps_fixtures.json
    # Related to Models
    python manage.py loaddata fixtures/objecttype_fixtures.json

    # This script goes through all app instances and assigns/removes permissions to users based on the instance access level
    python manage.py runscript app_instance_permissions
    
    # HELM deployment: DJANGO_SUPERUSER_PASSWORD should be an env var within the stackn-studio pod
    # python manage.py createsuperuser --email $DJANGO_SUPERUSER_EMAIL --username $DJANGO_SUPERUSER --no-input

    # ONLY for local testing with docker-compose
    python manage.py createsuperuser --email 'admin@test.com' --username 'admin' --no-input
    python manage.py runscript admin_token
fi

echo "Starting the Studio server..."

if $DEBUG ; then
    python manage.py runserver 0.0.0.0:8080
else
    python -m uvicorn studio.asgi:application --host 0.0.0.0 --port 8080
fi

# Alternative to be used:
# watchmedo auto-restart -R --patterns="*.py" -- daphne studio.asgi:application -b 0.0.0.0 -p 8080
# gunicorn studio.wsgi -b 0.0.0.0:8080 --reload

