import json
import os
import subprocess
import tarfile
import uuid

import yaml
from django.conf import settings

from .models import Apps

KUBEPATH = settings.KUBECONFIG


def delete(options):
    print("DELETE FROM CONTROLLER")
    # building args for the equivalent of helm uninstall command
    args = ["helm", "-n", options["namespace"], "delete", options["release"]]
    result = subprocess.run(args, capture_output=True)
    return result


def deploy(options):
    print("STARTING DEPLOY FROM CONTROLLER")
    _ = os.environ["BASE_PATH"]
    app = Apps.objects.get(slug=options["app_slug"], revision=options["app_revision"])
    if app.chart_archive and app.chart_archive != "":
        try:
            chart_file = settings.MEDIA_ROOT + app.chart_archive.name
            tar = tarfile.open(chart_file, "r:gz")
            extract_path = "/app/extracted_charts/" + app.slug + "/" + str(app.revision)
            tar.extractall(extract_path)
            tar.close()
            chart = extract_path
        except Exception as err:
            print(err)
            chart = "charts/" + options["chart"]
    else:
        chart = "charts/" + options["chart"]

    if "release" not in options:
        print("Release option not specified.")
        return json.dumps({"status": "failed", "reason": "Option release not set."})

    # Save helm values file for internal reference
    unique_filename = "charts/values/{}-{}.yaml".format(str(uuid.uuid4()), str(options["app_name"]))
    f = open(unique_filename, "w")
    f.write(yaml.dump(options))
    f.close()

    # building args for the equivalent of helm install command
    args = [
        "helm",
        "upgrade",
        "--install",
        "-n",
        options["namespace"],
        options["release"],
        chart,
        "-f",
        unique_filename,
    ]
    print("CONTROLLER: RUNNING HELM COMMAND... ")
    result = subprocess.run(args, capture_output=True)

    # remove file
    rm_args = ["rm", unique_filename]
    subprocess.run(rm_args)

    return result
