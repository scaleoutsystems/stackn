# Generated by Django 3.1.7 on 2021-04-09 14:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0052_remove_appinstance_release_name'),
        ('projects', '0029_auto_20210409_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='releasename',
            name='app',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='apps.appinstance'),
        ),
    ]
