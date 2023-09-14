#!/bin/bash

# Delete all data from database
# And restart the docker container
# There are some unique setup instructions that Nikita could not replicate here

docker exec studio bash -c "python manage.py flush --no-input"
docker restart studio
