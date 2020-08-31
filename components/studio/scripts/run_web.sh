#!/bin/bash
sleep 5
cd modules
echo "installing modules..."
for d in */ ; do
    echo "installing $d"
    python3 -m pip install -e $d
done
cd ..
# If we are running telepresence, use the correct settings.
[ ! -z "${TELEPRESENCE_ROOT}" ] &&  echo "Copy settings from Telepresence root directory" && \
    cp $TELEPRESENCE_ROOT/app/studio/settings.py studio/tele_settings.py && \
    export DJANGO_SETTINGS_MODULE=studio.tele_settings
# If we have set a local, custom settings.py, then use that.
[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings

echo "Installing all migrations"
python3 manage.py migrate

echo "loading seed data..."
python3 manage.py loaddata projects/fixtures/fixtures.json
python3 manage.py loaddata projects/fixtures/data.json
python3 manage.py loaddata deployments/fixtures/data.json

echo "starting serving..."
python3 manage.py runserver 0.0.0.0:8080
