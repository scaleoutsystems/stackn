# Generated by Django 2.2.13 on 2020-12-15 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0002_cluster_storageclass'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='quota',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='cluster',
            name='status',
            field=models.CharField(default='active', max_length=30),
        ),
    ]