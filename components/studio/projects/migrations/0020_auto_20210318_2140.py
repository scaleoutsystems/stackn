# Generated by Django 3.1.6 on 2021-03-18 21:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0019_mlflow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mlflow',
            name='access_key',
        ),
        migrations.RemoveField(
            model_name='mlflow',
            name='region',
        ),
        migrations.RemoveField(
            model_name='mlflow',
            name='s3_host',
        ),
        migrations.RemoveField(
            model_name='mlflow',
            name='secret_key',
        ),
        migrations.AddField(
            model_name='mlflow',
            name='s3',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='projects.s3'),
        ),
    ]
