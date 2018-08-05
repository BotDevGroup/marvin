#!/usr/bin/env python

from distutils.core import setup
import sys
from setuptools import find_packages


REQUIREMENTS = [
    'python-telegram-bot~=10.1.0',
    'blinker',
    'python-dateutil',
    'dogpile.cache~=0.6.2',
    'mongoengine',
    'polling',
    'pytz',
    'requests',
    'apscheduler',
    'flask',
    'flask-login',
    'flask-wtf',
    'passlib',
    'bcrypt',
    'requests-oauthlib',
]
if sys.platform.startswith('win'):
    REQUIREMENTS.append('pyreadline')

setup(name='marvinbot',
      version='0.5',
      description='Super Duper Telegram Bot - MK. III',
      author='BotDevGroup',
      author_email='',
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True,
      package_data={'': ['*.ini']},
      install_requires=REQUIREMENTS,
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      dependency_links=[

      ],)
