from setuptools import setup, find_packages
from scaleout import version


setup(
    name='scaleout-cli',
    version=version.__version__,
    description="""Scaleout CLI""",
    author='Morgan Ekmefjord',
    author_email='morgan@scaleout.se',
    url='https://www.scaleoutsystems.com',
    include_package_data=True,
    py_modules=['scaleout'],
    python_requires='>=3.5,<4',
    install_requires=[
        "attrdict>=2.0.1",
        "certifi>=2018.11.29",
        "chardet>=3.0.4",
        "Click>6.6",
        "cytoolz",
        "PyYAML>=4.2b1",
        "requests==2.23.0",
        "urllib3==1.24.2",
        "minio==5.0.6",
        "six>=1.14.0",
        "python-slugify",
        "prettytable",
        "pyjwt",
        "psutil"
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    entry_points={
        'console_scripts': ["stackn=scaleout.cli:main"]
    },
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
