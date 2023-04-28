# Delete all test users from e2e tests except for the contributor user
docker exec studio bash -c "python manage.py dbshell -- \
    -c \"DELETE FROM auth_user WHERE \
    username = 'e2e_tests_login_tester' OR username LIKE 'e2e_tests_signup_%'; \" "

# Create test user for login test
docker exec studio bash -c "python manage.py shell \
    -c \"from django.contrib.auth.models import User; \
    user = User.objects.create_user('e2e_tests_login_tester', 'no-reply-login@scilifelab.se', 'test12345'); user.save(); \"  "
