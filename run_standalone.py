#!/usr/bin/env ipython

import os
import sys
import signal
from pprint import pprint

from marvinbot import *
from marvinbot.models import *
from marvinbot.utils import get_config, load_sources, configure_mongoengine
from marvinbot.core import get_adapter, configure_adapter
from marvinbot.cache import configure_cache
from marvinbot.polling import TelegramPollingThread
from marvinbot.celeryapp import marvinbot_app
from marvinbot.signals import bot_started, bot_shutdown
import logging

LOG_FORMAT = '%(asctime)s %(levelname)s [%(processName)s/%(threadName)s|%(name)s] %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger('standalone-bot')


os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
configure_mongoengine(config)
configure_cache(config)
configure_adapter(config)


def real_shutdown():
    log.info('Shutting down...')
    bot_shutdown.send(adapter)
    adapter.updater_thread.stop()


def shutdown(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)

    try:
        if input("\nReally quit? (y/n)> ").lower().startswith('y'):
            real_shutdown()

    except KeyboardInterrupt:
        log.info("Ok ok, quitting")
        real_shutdown()
        sys.exit(1)

    # restore the exit gracefully handler here
    signal.signal(signal.SIGINT, shutdown)


def main(adapter):
    # The program will exit as soon as all non-daemon threads stop
    adapter.updater_thread.daemon = False
    log.info("Starting bot in standalone mode")
    adapter.updater_thread.start()
    load_sources(adapter.config, adapter)
    bot_started.send(adapter)


if __name__ == '__main__':
    # store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, shutdown)
    from marvinbot.tasks import *
    adapter = get_adapter()
    adapter.updater_thread = TelegramPollingThread(adapter)
    main(adapter)
