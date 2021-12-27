#!/bin/bash

# This script will load FEDn within STACKn

# Donwload FEDn folder and remove .svn from it
svn checkout https://github.com/carmat88/stackn-apps/trunk/FEDn
rm -rf FEDn/.svn/

# Loadind all fixtures related to FEDn
python3 manage.py loaddata FEDn/fixtures/project_template.json
python3 manage.py loaddata FEDn/fixtures/apps_fixtures.json

# Invoke script for upload FEDn apps logo - Passing relative path
python3 manage.py runscript load_apps_logo "./FEDn"

# Copy FEDn apps charts in default charts folder
cp -r FEDn/fedn-* ./charts/apps

# Removing comments from base template to show FEDn navbar item
sed -i "s/{% comment %}/ /g" projects/templates/projects/base.html
sed -i "s/{% endcomment %}/ /g" projects/templates/projects/base.html