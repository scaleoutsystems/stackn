from django.db import models
from django.contrib.auth.models import User
import uuid
import yaml
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify


class SessionManager(models.Manager):

    def generate_passkey(self, length=20):
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password

    def create_session(self, name, project, chart, settings, helm_repo=None):
        slug = slugify(name)
        key = self.generate_passkey()
        secret = self.generate_passkey(40)
        _sett = yaml.safe_dump(settings)
        status = 'CR'
        session = self.create(name=name,
                              project=project,
                              status=status,
                              slug=slug,
                              session_key=key,
                              session_secret=secret,
                              chart=chart,
                              settings=_sett,
                              helm_repo=helm_repo)

        return session


class Session(models.Model):

    objects = SessionManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512, unique=False)
    slug = models.CharField(max_length=512)
    CREATED = 'CR'
    STARTED = 'ST'
    STOPPED = 'SP'
    FINISHED = 'FN'
    ABORTED = 'AB'
    STATUS = [
        (CREATED, 'Created'),
        (STARTED, 'Started'),
        (STARTED, 'Stopped'),
        (FINISHED, 'Finished'),
        (ABORTED, 'Aborted'),
    ]
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='session')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')

    session_key = models.CharField(max_length=512)
    session_secret = models.CharField(max_length=512)
    settings = models.TextField()
    chart = models.CharField(max_length=512)
    helm_repo = models.CharField(max_length=1024, null=True, blank=True)

    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# class Chart(models.Model):
#    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#    name = models.CharField(max_length=512, unique=False)

#    created_at = models.DateTimeField(auto_now_add=True)
#    updated_at = models.DateTimeField(auto_now=True)
