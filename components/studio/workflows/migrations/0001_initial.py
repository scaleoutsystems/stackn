# Generated by Django 2.2.13 on 2020-08-31 08:56

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowDefinition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512, unique=True)),
                ('definition', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('CR', 'Created'), ('ST', 'Started'), ('ST', 'Stopped'), ('FN', 'Finished'), ('AB', 'Aborted')], default='CR', max_length=2)),
                ('name', models.CharField(max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project', to='projects.Project')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_definition', to='workflows.WorkflowDefinition')),
            ],
        ),
    ]