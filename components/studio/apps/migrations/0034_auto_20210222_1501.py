# Generated by Django 3.1.6 on 2021-02-22 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0033_resourcedata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcedata',
            name='time',
            field=models.IntegerField(verbose_name='timestamp'),
        ),
    ]
