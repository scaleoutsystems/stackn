#!/bin/bash
sleep 5

# If we are running telepresence, use the correct settings.
[ ! -z "${TELEPRESENCE_ROOT}" ] &&  echo "Copy settings from Telepresence root directory" && \
    cp $TELEPRESENCE_ROOT/app/studio/settings.py studio/tele_settings.py && \
    export DJANGO_SETTINGS_MODULE=studio.tele_settings

# If we have set a local, custom settings.py, then use that.
[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings

echo "Installing all migrations"
python3 manage.py migrate

# echo "loading seed data..."
# python3 manage.py loaddata projects/fixtures/fixtures.json
# python3 manage.py loaddata projects/fixtures/data.json
# python3 manage.py loaddata deployments/fixtures/data.json
# python3 manage.py loaddata appcats_fixtures.json
# python3 manage.py loaddata apps_fixtures.json


echo "starting serving..."
if [ -z "${DEBUG}" ] && [ -z "${TELEPRESENCE_ROOT}" ]; then
    gunicorn studio.wsgi -b 0.0.0.0:8080 -w 4
else
    # watchmedo auto-restart -R --patterns="*.py" -- daphne studio.asgi:application -b 0.0.0.0 -p 8080
    python3 manage.py runserver 0.0.0.0:8080
    # gunicorn studio.wsgi -b 0.0.0.0:8080 --reload
fi

