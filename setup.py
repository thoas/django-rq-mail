# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = __import__('rq_mail').__version__

setup(
    name='django-rq-mail',
    version=version,
    description='simple Python library based on rq to store emails sent by Django and process them in the background with workers',
    author='Florent Messa',
    author_email='florent.messa@gmail.com',
    url='http://github.com/thoas/django-rq-mail',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)
