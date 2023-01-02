# studio-monitor

Monitor Django module for [Studio/STACKn](https://github.com/scaleoutsystems/stackn). To include source package in a Django project:

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install .
```
And add to installed apps in settings.py:

```
INSTALLED_APPS=[
    "monitor"
]
```

For a complete project follow the link above and navigate to settings.py