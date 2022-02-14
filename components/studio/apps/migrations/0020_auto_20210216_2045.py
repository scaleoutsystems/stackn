# Generated by Django 2.2.13 on 2021-02-16 20:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_volume'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apps', '0019_apps_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public', models.BooleanField(default=False)),
                ('projects', models.ManyToManyField(to='projects.Project')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='appinstance',
            name='permission',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='apps.AppPermission'),
        ),
    ]