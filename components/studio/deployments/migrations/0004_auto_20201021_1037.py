# Generated by Django 2.2.13 on 2020-10-21 10:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0003_auto_20200901_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deploymentinstance',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]