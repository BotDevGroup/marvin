from marvinbot.core import load_sources
from marvinbot.signals import bot_shutdown, bot_started
from marvinbot.polling import TelegramPollingThread
import logging

log = logging.getLogger(__name__)


def shutdown_bot(adapter):
    log.info('Shutting down...')
    adapter.updater_thread.stop()
    bot_shutdown.send(adapter)


def run_bot(adapter):
    # The program will exit as soon as all non-daemon threads stop
    adapter.updater_thread = TelegramPollingThread(adapter)
    adapter.updater_thread.daemon = False

    log.info("Starting bot in standalone mode")
    adapter.updater_thread.start()
    load_sources(adapter.config, adapter)
    bot_started.send(adapter)
