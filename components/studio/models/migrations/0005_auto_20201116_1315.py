# Generated by Django 2.2.13 on 2020-11-16 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0004_auto_20201116_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modellog',
            name='training_started_at',
            field=models.CharField(max_length=255),
        ),
    ]