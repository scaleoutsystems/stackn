from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse

import pytest
from portal import views


@pytest.mark.django_db
def test_index():
    # Get correct request
    request = RequestFactory().get(reverse("portal:index"))

    # Create session
    s = SessionStore()

    # Add session to request
    request.session = s

    # Get response. Since index is a function, this is the correct way
    response = views.index(request)

    # Check if it returns the correct status code
    assert response.status_code == 200


def test_home_view_class():
    # Get correct request
    request = RequestFactory().get(reverse("portal:home"))

    # Get response. Since HomeView is a class, this is the correct way
    response = views.HomeView.as_view()(request)

    # Check status code
    assert response.status_code == 200
