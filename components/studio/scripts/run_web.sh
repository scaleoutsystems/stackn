#!/bin/sh
sleep 5
cd modules
echo "installing modules..."
for d in */ ; do
    echo "installing $d"
    python3 -m pip install -e $d
done
cd ..
python3 manage.py makemigrations
python manage.py makemigrations datasets deployments experiments files ingress labs models projects reports workflows
python3 manage.py migrate
echo "loading seed data..."
python3 manage.py loaddata projects/fixtures/users.json
python3 manage.py loaddata projects/fixtures/data.json
echo "starting serving..."
python3 manage.py runserver 0.0.0.0:8080
