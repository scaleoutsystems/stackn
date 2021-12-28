#!/bin/bash
# This script will load FEDn within STACKn by:

# Donwloading FEDn folder and remove .svn from it
svn checkout https://github.com/carmat88/stackn-apps/trunk/FEDn
rm -rf FEDn/.svn/

# Loading all fixtures related to FEDn
python3 manage.py loaddata FEDn/fixtures/project_template.json
python3 manage.py loaddata FEDn/fixtures/apps_fixtures.json

# Invoking script to upload FEDn apps logo (given a relative path)
python3 manage.py runscript load_apps_logo --script-args "./FEDn"

# Copying FEDn apps charts in default charts folder
cp -r FEDn/fedn-* ./charts/apps

# Removing comments from base template to show FEDn navbar item
sed -i "s/{% comment %}/ /g" projects/templates/projects/base.html
sed -i "s/{% endcomment %}/ /g" projects/templates/projects/base.html