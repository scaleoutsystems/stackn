from os import path
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from projects.models import Project, Environment
from models.models import Model
from .models import ReportGenerator
from .models import Report
from .helpers import upload_report_json, get_download_link
from studio.minio import MinioRepository, ResponseError

minio_repository = MinioRepository(url='play.min.io',
                                   access_key='Q3AM3UQ867SPQQA43P2F',
                                   secret_key='zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG')
minioClient = minio_repository.client


class ReportTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="admin")
        environment = Environment.objects.create(
            name="test-project-env",
            image="test-project-env"
        )
        project = Project.objects.create(
            name="test-project",
            slug="test-project",
            owner=user,
            project_key="key",
            project_secret="secret",
            environment=environment
        )
        model = Model.objects.create(
            uid="uid",
            name="test-model",
            project=project
        )
        generator = ReportGenerator.objects.create(
            project=project,
            generator="generator.py",
            visualiser="visualiser.py"
        )
        Report.objects.create(
            model=model,
            job_id="job_id",
            generator=generator
        )

    def test_upload_report_json(self):
        report = Report.objects.filter(job_id='job_id').first()

        if not minioClient.bucket_exists('reports'):
            minioClient.make_bucket('reports', location="us-east-1")

        upload_report_json(report.pk, minioClient)

        found = False
        try:
            minioClient.stat_object('reports', 'report_{}.json'.format(report.pk))
            found = True
        except ResponseError as err:
            print(err)

        self.assertEqual(found, True)

        local_found = path.exists('reports/report_{}.json'.format(report.pk))

        self.assertNotEqual(local_found, True)

    def test_get_download_link(self):
        report = Report.objects.filter(job_id='job_id').first()
        project = report.model.project

        filename = 'report_{}.json'.format(report.pk)

        download_link = minioClient.presigned_get_object('reports', filename, expires=timedelta(days=2))

        self.assertEqual(download_link, get_download_link(project.pk, filename, minioClient))
