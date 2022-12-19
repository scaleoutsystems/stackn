from setuptools import find_packages, setup

setup(
    name="studio-api",
    version="0.0.1",
    description="""Django app for handling REST-API in Studio""",
    url="https://www.scaleoutsystems.com",
    include_package_data=True,
    py_modules=["api"],
    python_requires=">=3.6,<4",
    install_requires=[
        "django==4.0.6",
        "requests==2.27.1",
        "Pillow==9.0.0",
        "django-guardian==2.4.0",
        "Markdown==3.3.6",
        "django-tagulous==1.3.3",
        "minio==7.0.2",
        "s3fs==2022.1.0",
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    keywords="",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
