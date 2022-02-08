# Generated by Django 3.2.7 on 2022-02-07 20:37

from django.db import migrations, models
import tagulous.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0059_auto_20210719_1406'),
    ]

    operations = [
        migrations.AddField(
            model_name='appinstance',
            name='description',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='appinstance',
            name='tags',
            field=tagulous.models.fields.TagField(_set_tag_meta=True, blank=True, help_text='Enter a comma-separated tag string', null=None, to='apps.Tagulous_AppInstance_tags'),
        ),
    ]
