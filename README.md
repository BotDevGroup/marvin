![Python 3.5](https://img.shields.io/badge/python-3.5-blue.svg) ![License](https://img.shields.io/github/license/mashape/apistatus.svg)
# Marvin
Telegram Bot written in Python

# Requirements

- [Python 3.5](https://www.python.org/downloads/release/python-352/)
- [MongoDB](https://www.mongodb.com/download-center#community)

## Optional requirements:
- Memcached([Windows](https://commaster.net/content/installing-memcached-windows)/[Ubuntu](https://memcached.org/downloads)/Mac just: $ brew install memcached) 

You'll need RabbitMQ if you want to run the bot with Celery support

Memcached is need if you need real caching, remember to install a python
driver (pylibmc or python-memcached) and adjust your settings accordingly. 

# Getting started

####OS installation guide at the end.

Download the source with:

    $ git clone git@github.com:BotDevGroup/marvin.git

Install the bot with:

    (venv)$ python setup.py develop
    
Copy `default_settings.<your platform>.json` and rename it to `settings.json` (Open `settings.json` to customize it).
Remember to set your Telegram bot token on `telegram_token`, as well as the urls for memcached/rabbitmq.
This is also a good time to add any plugins.

    $ cp default_settings.linux.json settings.json
    
    
# Running the bot:

## Normal run 

To start the bot:

    (venv)$ ./marvind start
    
To stop the bot:

    (venv)$ ./marvind stop
    
To tail the logs:

    (venv)$ ./marvind bot_log
    
## Running in standalone mode [For dev]

This mode is for dev purposes and for people running on Windows who don't have
proper shell facilities.

To start the bot:

    (venv)$ python run_standalone.py
    
This will bring the bot up in the current shell, to exit just hit `Ctrl+C` and
confirm.

Running in this mode only requires MongoDB to be running.
    
## Shell

If you want a shell and a great debugger:
    
    $ ./marvind shell


####How to setup your Bot

1. Go ahead and talk to [@BotFather](https://telegram.me/BotFather) to generate your bot token key.
2. Now that you have your token already generated go to settings.json and add your token to `"telegram_token": "Your Token Goes Here"`
3. Make sure you have rabbitmq and memcached installed in your system. 
4. Go to the directory of the bot in your terminal and type `./marvind start`.
5. Now open Telegram, go to your bot and say '/test' :)



Other references:
- [Telegram API documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot documentation](https://pythonhosted.org/python-telegram-bot/)

# OS installation guide

###Linux 
This article assumes that you have user with sudo privileges. (DON'T USE ROOT FOR DEVELOPMENT)

######Step one - Install python 3.5, rabbitmq, memcached, pip, celery and others.

#####Ubuntu 
(tested in Ubuntu 16.04)

	$ sudo apt-get install git python3.5 python3-all-dev python3-pylibmc python3-pip python3-celery python3-dogpile.cache python3-dateutil python3-sqlalchemy python3-blinker memcached 
	$ sudo apt-get install -y libmemcached-dev zlib1g-dev libssl-dev python-dev build-essential

#####Arch Linux
    $ sudo pacman -S memcached mongodb libmemcached boost

Step two - Install `mongoengine`:

Check for celery if is the requirement version:

	$ pip install mongoengine

Step three - Install `virtualenv`:

	$ sudo pip install virtualenv
	$ virtualenv --python=`which python3` venv	# Where venv will be the virtualenv folder.
	
Activate the `virtualenv`. Remember to run this inside the project:

	$ source venv/bin/activate

You should now see `(venv) user@host:~$`.


# Making Plugins

See the [sample plugin](https://github.com/BotDevGroup/marvinbot_sample_plugin)


# Contributing

Contributions of all sizes are welcome. Please review our [contribution guidelines](https://github.com/BotDevGroup/marvin/blob/master/CONTRIBUTING.md) to get started. You can also help by [reporting bugs](https://github.com/BotDevGroup/marvin/issues/new).
