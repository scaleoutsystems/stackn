#!/bin/bash

# v0.1.0
# Script can be improved by for example taking into account that this works only first time!
# One approach could be to ask the user input for specific values each time the command docker-compose up runs
# Later times strings such as <your-domain.com> will already be overwritten, so sed commands will not work
set -e

if [ -z $1 ]; then 

    echo "Would you like to use localhost(127.0.0.1) as host? Observe, while great for development some features of STACKn will not work properly with localhost. [yes | no]"
    read host
    if [ $host != "yes" -a $host != "no" ]; then
        echo "Incorrect value: $host. Allowed values are: [yes | no]"
    fi
    echo "Set internal IP (needed for ingress controller to contact webserver). If left empty this script will attempt to get it for you."
    read internal_ip

    echo "(optional) Set external (public) IP. If you like to reach the webserver from the outside. Observe that security measures is up to the admin of this deployment."
    read external_ip

    echo "HOST: $host"
    echo "EXTERNAL_IP: $external_ip"
    echo "INTERNAL_IP: $internal_ip"
else
    host="no"
fi

if [ -z $internal_ip ]; then
    echo "Extracting IP address..."
    internal_ip=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')
    echo "Your current IP address is: $internal_ip"
fi

if [ $host = "yes" ]; then
    ip="127.0.0.1"
else
    ip=$internal_ip
fi

echo "Running the utility script for setting up initial values"

# Generate k8s cluster config file - NOTE: we assume that microk8s is already installed and configured
echo ""
echo "Copying k8s cluster config values into the cluster.conf file"
echo ""
sudo microk8s.config > ./cluster.conf

# Extract used network interface - Just for sysadmin purposes
#my_interface=$(ip route get 8.8.8.8 | awk -F"dev " 'NR==1{split($2,a," ");print a[1]}')

# Replace <your-domain.com> field with extracted IP adress in values.yaml file
echo "Replacing $ip within settings.py ..."
echo "Appending nip.io wildcards..."
echo "Replacing values:"
echo "DOMAIN = '$ip.nip.io'"
sed -i "s/<your-domain>/$ip.nip.io/g" ./studio/settings.py
echo "AUTH_DOMAIN = '$internal_ip.nip.io'"
sed -i "s/AUTH_DOMAIN = '$ip.nip.io'/AUTH_DOMAIN = '$internal_ip.nip.io'/g" ./studio/settings.py

if [ ! -z $external_ip ]; then
    echo "STUDIO_URL = 'http://studio.$external_ip.nip.io:8080'"
    sed -i "s/STUDIO_URL = 'http:\/\/studio.$ip.nip.io:8080'/STUDIO_URL = 'http:\/\/studio.$external_ip.nip.io:8080'/g" ./studio/settings.py
    echo "SESSION_COOKIE_DOMAIN = '.$external_ip.nip.io'"
    sed -i "s/SESSION_COOKIE_DOMAIN = '.$ip.nip.io'/SESSION_COOKIE_DOMAIN = '.$external_ip.nip.io'/g" ./studio/settings.py

    echo "Your current STACKn URL will be: http://studio.$external_ip.nip.io:8080"
else
    echo "STUDIO_URL = 'http://studio.$ip.nip.io:8080'"
    echo "SESSION_COOKIE_DOMAIN = '.$ip.nip.io'"
    echo ""
    echo "Your current STACKn URL will be: http://studio.$ip.nip.io:8080"
fi

echo "Done! Please start STACKn with: docker-compose up"