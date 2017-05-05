![Python 3.5](https://img.shields.io/badge/python-3.5-blue.svg) ![License](https://img.shields.io/github/license/mashape/apistatus.svg)
# Marvin
Bot framework with plugin capability written in Python.

# Requirements

- [Python 3.5](https://www.python.org/downloads/release/python-352/)
- [MongoDB](https://www.mongodb.com/download-center#community)

## Optional requirements:
- Memcached([Windows](https://commaster.net/content/installing-memcached-windows)/[Ubuntu](https://memcached.org/downloads)/Mac just: $ brew install memcached) 

Memcached is need if you need real caching, remember to install a python
driver (pylibmc or python-memcached) and adjust your settings accordingly. 

# OS Installation Guide

See the [guide for installation](https://github.com/BotDevGroup/marvin/wiki/Installation).

# Running Marvin
See the [guide to run marvin](https://github.com/BotDevGroup/marvin/wiki/Running-marvin).


# Running tests

First run:

    $ ./marvind test
    
You can just run nosetests directly afterwards:

    $ nosetests


# Making Plugins

See the [sample plugin](https://github.com/BotDevGroup/marvinbot_sample_plugin).  
See the [guide for plugins](https://github.com/BotDevGroup/marvin/wiki/Plugins).


# Contributing

Contributions of all sizes are welcome. Please review our [contribution guidelines](https://github.com/BotDevGroup/marvin/blob/master/CONTRIBUTING.md) to get started. You can also help by [reporting bugs](https://github.com/BotDevGroup/marvin/issues/new).
