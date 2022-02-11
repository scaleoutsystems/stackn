#!/bin/bash

# v0.1.0
# Script can be improved by for example taking into account that this works only first time!
# One approach could be to ask the user input for specific values each time the command docker-compose up runs
# Later times strings such as <your-domain.com> will already be overwritten, so sed commands will not work

set -e

echo "Running the utility script for setting up initial values"

# Generate k8s cluster config file - NOTE: we assume that microk8s is already installed and configured
echo "Copying k8s cluster config values into the cluster.conf file"
microk8s.config > ./cluster.conf

# Extract currently assigned IP address (which is connected to Internet!)
echo "Extracting IP address..."
my_ip=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')
echo "Your current IP address is: $my_ip"

# Extract used network interface - Just for sysadmin purposes
#my_interface=$(ip route get 8.8.8.8 | awk -F"dev " 'NR==1{split($2,a," ");print a[1]}')

# Replace <your-domain.com> field with extracted IP adress in values.yaml file
echo "Replacing $my_ip within the docker-compose.yaml and settings.py files..."
echo "Appending nip.io wildcards..."
sed -i "s/<your-domain>/$my_ip.nip.io/g" ./docker-compose.yml
sed -i "s/<your-domain>/$my_ip.nip.io/g" ./studio/settings.py
echo "Your current STACKn domain will be: $my_ip.nip.io"

echo "Done"