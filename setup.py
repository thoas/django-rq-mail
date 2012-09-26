# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

version = __import__('rq_mail').__version__

root = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root, 'README.rst')) as f:
    README = f.read()

setup(
    name='django-rq-mail',
    version=version,
    description='simple Python library based on rq to store emails sent by Django and process them in the background with workers',
    long_description=README,
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
