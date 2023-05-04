# Create test user for contribution tests
docker exec studio bash -c "python manage.py shell \
    -c \"from django.contrib.auth.models import User; \
    user = User.objects.create_user('e2e_tests_contributor_tester', 'no-reply-contributor@scilifelab.se', 'test12345'); user.save(); \"  "
