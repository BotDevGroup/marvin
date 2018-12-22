#!/usr/bin/env python
from marvinbot.log import configure_logging
from marvinbot.utils import get_config, configure_mongoengine
from marvinbot.cache import configure_cache
import logging
import os
import sys
import signal

if sys.platform.startswith("win"):
    import pyreadline as readline
else:
    import readline


log = logging.getLogger("marvinbot-runner")

# os.environ["PYTHONINSPECT"] = "True"
config = get_config()
configure_logging(config)
configure_mongoengine(config)
configure_cache(config)

from marvinbot.core import get_adapter, configure_adapter
from marvinbot.runner import run_bot, shutdown_bot
from marvinbot.net import configure_downloader

configure_adapter(config)
configure_downloader(config)

original_sigint = None


def confirm_shutdown(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)

    try:
        if input("\nReally quit? (y/n)> ").lower().startswith("y"):
            shutdown_bot(adapter)

    except KeyboardInterrupt:
        log.info("Ok ok, quitting")
        shutdown_bot(adapter)
        sys.exit(1)

    # restore the exit gracefully handler here
    signal.signal(signal.SIGINT, confirm_shutdown)


def terminate(signum, frame):
    shutdown_bot(adapter)


if __name__ == "__main__":
    # store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, confirm_shutdown)
    signal.signal(signal.SIGTERM, terminate)
    adapter = get_adapter()
    from marvinbot.tasks import *

    run_bot(adapter)
