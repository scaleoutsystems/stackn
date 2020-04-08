from setuptools import setup, find_packages

setup(
    name='scaleout-proto',
    version='0.0.2',
    description="""Scaleout proto""",
    author='Morgan Ekmefjord',
    author_email='morgan@scaleoutsystems.com',
    url='https://www.scaleoutsystems.com',
    include_package_data=True,
    py_modules=['proto'],
    setup_requires=['setuptools-markdown'],
    python_requires='>=3.5,<4',
    install_requires=[
        "grpc_tools==0.0.1",
        "grpcio==1.27.1",
        "six==1.14.0",
        "protobuf==3.11.3",
        "pypandoc",
        "wheel",
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    keywords='',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
