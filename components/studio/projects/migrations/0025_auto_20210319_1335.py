# Generated by Django 3.1.6 on 2021-03-19 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0024_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=512),
        ),
    ]
