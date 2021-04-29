import os
from datetime import timedelta

from .jobs import get_logs
from .models import Report
import json
import subprocess
from studio.minio import MinioRepository, ResponseError
from projects.models import Project, ProjectLog
import logging
from projects.helpers import get_minio_keys

logger = logging.getLogger(__name__)


def upload_report_json(report_id, client=None):
    report = Report.objects.filter(pk=report_id).first()
    project = report.model.project

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    report_json = {
        'project_id': project.id,
        'model_id': report.model.id,
        'model_uid': report.model.uid,
        'description': report.description,
        'report': report.report
    }

    filename = 'reports/report_{}.json'.format(report_id)
    with open(filename, 'w') as json_file:
        json.dump(report_json, json_file)

    try:
        if not client:
            minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), decrypted_key,
                                               decrypted_secret)

            client = minio_repository.client

        with open(filename, 'rb') as file_data:
            file_stat = os.stat(filename)
            client.put_object('reports', filename.replace('reports/', ''), file_data,
                              file_stat.st_size, content_type='application/json')

            l = ProjectLog(project=project, module='RE', headline='Metrics',
                           description='JSON file {filename} has been uploaded to MinIO'.format(
                               filename=filename.replace('reports/', '')))
            l.save()

    except ResponseError as err:
        print(err)

    os.unlink(filename)


def populate_report_by_id(report_id):
    report = Report.objects.filter(pk=report_id).first()

    # Check the logs for the k8s job and if done, update the report object's field.
    try:
        result = get_logs(report.job_id)
        if result:
            report.report = result
            report.status = 'C'
            report.save()

            upload_report_json(report.id)

            # Generate an image with the classification report.
            subprocess.run(["python", "reports/{}".format(report.generator.visualiser), report.report, str(report.id)])

    except Exception as e:
        print(e)


def get_visualiser_file(project_id, filename):
    project = Project.objects.filter(pk=project_id).first()

    content = None
    import requests as r
    url = 'http://{}-file-controller/file/{}'.format(project.slug, filename)
    try:
        response = r.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload['status'] == 'OK':
                content = payload['content']
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    if content:
        with open("reports/{}".format(filename), "w") as new_file:
            new_file.write(content)


def get_download_link(project_id, filename, client=None):
    project = Project.objects.filter(pk=project_id).first()

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    download_link = None
    try:
        if not client:
            minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), decrypted_key,
                                               decrypted_secret)

            client = minio_repository.client

        download_link = client.presigned_get_object('reports', filename, expires=timedelta(days=2))
    except ResponseError as err:
        print(err)

    return download_link
