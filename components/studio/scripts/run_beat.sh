cd modules
for d in */ ; do
    echo "installing $d"
    python3 -m pip install -e $d
done
cd ..

#[ ! -z "${TELEPRESENCE_ROOT}" ] &&  echo "Copy settings from Telepresence root directory" && \
#    cp $TELEPRESENCE_ROOT/app/studio/settings.py studio/tele_settings_worker.py && \
#    export DJANGO_SETTINGS_MODULE=studio.tele_settings_worker
## If we have set a local, custom settings.py, then use that.
#[ -f studio/local_settings.py ] && echo "Using local settings file" && export DJANGO_SETTINGS_MODULE=studio.local_settings


sleep 1

watchmedo auto-restart -R --patterns="*.py" -- celery -A studio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler