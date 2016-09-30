![Python 3.5](https://img.shields.io/badge/python-3.5-blue.svg) ![License](https://img.shields.io/github/license/mashape/apistatus.svg)
# Marvin
Telegram Bot written in Python

# Requirements

- [Python 3.5](https://www.python.org/downloads/release/python-352/)
- [RabbitMQ](https://www.rabbitmq.com/download.html)
- Memcached ([Windows](https://commaster.net/content/installing-memcached-windows)/[Ubuntu](https://memcached.org/downloads))
- [MySQL](http://dev.mysql.com/downloads/)/[MariaDB](https://downloads.mariadb.org/)

# Getting started

####OS installation guide at the end.

Download the source with:

    $ git clone git@github.com:BotDevGroup/marvin.git

Install the bot with:

    $ python setup.py develop
    
Copy `default_settings.<your platform>.json` and rename it to `settings.json` (Open `settings.json` to customize it).
Remember to set your Telegram bot token on `telegram_token`, as well as the urls for memcached/rabbitmq.
This is also a good time to add any plugins.

    $ cp default_settings.linux.json settings.json
    
To start the bot:

    $ ./marvind start
    
To stop the bot:

    $ ./marvind stop
    
To tail the logs:

    $ ./marvind celery_log

If you want a shell and a great debugger:
    
    $ pip install ipython ipdb
    $ ./marvind shell


####How to setup your Bot

1. Go ahead and talk to [@BotFather](https://telegram.me/BotFather) to generate your bot token key.
2. Now that you have your token already generated go to settings.json and add your token to `"telegram_token": "Your Token Goes Here"`
3. Make sure you have rabbitmq and memcached installed in your system. 
4. Go to the directory of the bot in your terminal and type `./marvind start`, once the bot has started, you'll see a message saying "OK". 
5. Now open Telegram, go to your bot and say '/hello' :)



Other references:
- [Telegram API documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot documentation](https://pythonhosted.org/python-telegram-bot/)

# OS installation guide
####Ubuntu 
(tested in Ubuntu 16.04)

This article assumes that you have user with sudo privileges. (DON'T USE ROOT FOR DEVELOP)

Step one - Install python 3.5, rabbitmq, memcached, pip, celery and others:

	$ sudo apt-get install git python3.5 python3-all-dev python3-pylibmc python3-pip python3-celery python3-dogpile.cache python3-dateutil python3-sqlalchemy python3-blinker rabbitmq-server memcached 
	$ sudo apt-get install -y libmemcached-dev zlib1g-dev libssl-dev python-dev build-essential

Check for celery if is the requirement vertion:

	$ pip install --upgrade "celery==3.1.23"

Install `mongoengine` module:

	$ pip install mongoengine

Install `pylibmc`:

	$ pip install pylibmc

Step two - Install `virtualenv`:

	$ sudo pip install virtualenv
	$ virtualenv --python=`which python3` venv	# Where venv will be the virtualenv folder.
	
Activate the `virtualenv`. Remember to run this inside the project:

	$ source venv/bin/activate

You should see now `(venv) user@host:~$`.



# Contributing

Contributions of all sizes are welcome. Please review our [contribution guidelines](https://github.com/BotDevGroup/python-telegram-bot/blob/master/CONTRIBUTING.md) to get started. You can also help by [reporting bugs](https://github.com/BotDevGroup/python-telegram-bot/issues/new).
