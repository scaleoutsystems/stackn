#!/usr/bin/env bash

cd modules
for d in */ ; do
    echo "installing $d"
    python3 -m pip install -e $d
done
cd ..

sleep 30

celery -A studio worker -l info