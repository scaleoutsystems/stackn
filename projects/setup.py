from setuptools import setup

setup(
    name="studio-projects",
    version="0.0.1",
    description="""Django app for handling portal in Studio""",
    url="https://www.scaleoutsystems.com",
    include_package_data=True,
    package=["projects"],
    package_dir={"projects": "."},
    python_requires=">=3.6,<4",
    install_requires=[
        "django==4.2.1",
        "requests==2.31.0",
        "django-guardian==2.4.0",
        "celery==5.2.7",
        "Pillow==9.4.0",
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    keywords="",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
