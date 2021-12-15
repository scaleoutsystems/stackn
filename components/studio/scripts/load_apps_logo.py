# Currently Apps are pre-populated via django fixtures (as json files)
# However files cannot be uploade into the db via json. This utility script does that.
from apps.models import Apps
from django.conf import settings
from django.core.files import File

import os
import subprocess

def run():
    # Fetching the charts path from settings.py and create a list of all the apps folder
    subfolders = [f.path for f in os.scandir(settings.CHART_FOLDER) if f.is_dir()]
    subfolders.sort()
    curr_dir = os.getcwd()

    # In each folder there should be a logo image called 'logo.png'
    for folder in subfolders:
        os.chdir(folder)
        file_to_upload = File(open('logo.png','rb'))    # every chart folder should have a logo file as logo.png
        tail = os.path.split(os.getcwd())[1] # e.g. "/app/charts/apps/jupyter-lab" -> tail = "jupyter-lab"
        new_filename=tail+"-logo.png"
        curr_app = Apps.objects.get(slug=tail)
        curr_app.logo_file.save(new_filename, file_to_upload)
        file_to_upload.close()
        os.chdir(curr_dir)
