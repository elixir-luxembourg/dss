#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

requirements = [
    'Flask', 'Flask-Assets', 'Flask-SQLAlchemy', 'Flask-Script', 'Jinja2', 'SQLAlchemy', 'Werkzeug', 'closure',
    'cssmin', 'webassets', 'Flask-Testing', 'requests',
    'Flask-Cache',
    'Flask-Login', 'Flask-WTF', 'Flask-Migrate',
    'sqlalchemy-utils', 'Flask-Security', 'Flask-Mail', 'Flask-Babel'
]

test_requirements = [
    'coverage'
]

setup(
    name='elixir-dcp',
    version='0.0.1-dev',
    description="Elixir-LU Data and Computing Platform",
    author="Valentin Grouès",
    author_email='valentin.groues@uni.lu',
    url='https://git-r3lab.uni.lu/elixir/elixir-dcp',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'elixir_dcp':
                     'elixir_dcp'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords=['elixir'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        # 'Intended Audience :: Developers',
        # 'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    package_data={
        'elixir-dcp': ['elixir_dcp/resources/*']
    },
    extras_require={
        'dev': [
            'tox',
            'pep8',
            'bumpversion',
            'coverage'
        ]
    }
)
