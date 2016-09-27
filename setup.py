#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

REQUIREMENTS = [
    'python-telegram-bot'
    'celery',
    'sqlalchemy',
    'blinker',
    'python-dateutil',
]

setup(name='bottob',
      version='0.1',
      description='Super Duper Telegram Bot - MK. III',
      author='BotDevGroup',
      author_email='',
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True,
      package_data={'': ['*.ini']},
      # namespace_packages=["telegrambot",],
      install_requires=REQUIREMENTS,
      dependency_links=[

      ],)
