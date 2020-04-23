#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

requirements = [
    'Flask==1.1.2',
    'Flask-Assets==2.0',
    'Flask-SQLAlchemy==2.4.1',
    'Flask-Script==2.0.6',
    'Jinja2==2.11.1',
    'SQLAlchemy==1.3.16',
    'Werkzeug==1.0.1',
    'closure==20191111',
    'flask-caching',
    'Flask-Login',
    'Flask-WTF==0.14.3',
    'Flask-Migrate',
    'flask-oidc',
    'Flask-Testing==0.8.0',
    'sqlalchemy-utils',
    'Flask-Mail',
    'Flask-Babel',
    'cssmin',
    'webassets',
    'requests',
    'pdfkit',
    'flask_wkhtmltopdf',
    'psycopg2==2.7.7',
    'WTForms-Components==0.10.4',
    'schedule',
    'WTForms==2.2.1'
]

test_requirements = [
    'coverage'
]

setup(
    name='elixir-dcp',
    version='0.3.0-dev',
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
