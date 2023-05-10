from django.core.management.base import BaseCommand, CommandError

from projects.models import Project


class Command(BaseCommand):
    help = """This script removes all projects
    (and all objects belonging to the projects) with status deleted"""

    def handle(self, *args, **options):
        qs = Project.objects.filter(status="deleted")

        for project in qs:
            try:
                self.stdout.write(f"Deleting project: {project.name}")
                project.delete()
            except Exception:
                raise CommandError("Failed to delete project")

        self.stdout.write(self.style.SUCCESS("Success!"))
