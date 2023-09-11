import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from django.urls import reverse

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
    assert "<title>Overview | SciLifeLab Serve</title>" in response.content.decode()


def test_home_view_class():
    # Get correct request
    request = RequestFactory().get(reverse("portal:home"))

    # Get response. Since HomeView is a class, this is the correct way
    response = views.HomeView.as_view()(request)

    # Check status code
    assert response.status_code == 200
    assert "<title>Home | SciLifeLab Serve</title>" in response.content.decode()


def test_about_view():
    # Get correct request
    request = RequestFactory().get(reverse("portal:about"))
    response = views.about(request)

    # Check status code
    assert response.status_code == 200
    assert "<title>About | SciLifeLab Serve</title>" in response.content.decode()


def test_teaching_view():
    # Get correct request
    request = RequestFactory().get(reverse("portal:teaching"))
    response = views.teaching(request)

    # Check status code
    assert response.status_code == 200
    assert "<title>Teaching | SciLifeLab Serve</title>" in response.content.decode()


def test_privacy_view():
    # Get correct request
    request = RequestFactory().get(reverse("portal:privacy"))
    response = views.privacy(request)

    # Check status code
    assert response.status_code == 200
    assert "<title>Privacy policy | SciLifeLab Serve</title>" in response.content.decode()
