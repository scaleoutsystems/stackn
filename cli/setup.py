from setuptools import find_packages, setup

setup(
    name='scaleout-cli',
    version='0.2.0',
    description="""Scaleout CLI""",
    url='https://www.scaleoutsystems.com',
    include_package_data=True,
    py_modules=['stackn'],
    python_requires='>=3.5,<4',
    install_requires=[
        "attrdict>=2.0.1",
        "certifi>=2018.11.29",
        "chardet>=3.0.4",
        "click==7.1.2",
        "cytoolz",
        "PyYAML>=4.2b1",
        "requests",
        "urllib3>=1.26.5",
        "minio==7.0.2",
        "six>=1.14.0",
        "python-slugify",
        "prettytable",
        "pyjwt",
        "psutil"
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    entry_points={
        'console_scripts': ["stackn=stackn:main"]
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
