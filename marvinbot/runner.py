from marvinbot.plugins import load_plugins
from marvinbot.signals import bot_shutdown, bot_started
from marvinbot.polling import TelegramPollingThread
from marvinbot.scheduler import configure_scheduler
import logging

log = logging.getLogger(__name__)


def shutdown_bot(adapter):
    log.info('Shutting down...')
    if adapter.scheduler_available:
        adapter.scheduler.shutdown()
    adapter.updater.stop()
    bot_shutdown.send(adapter)


def run_bot(adapter):
    # The program will exit as soon as all non-daemon threads stop
    log.info("Starting bot in standalone mode")
    adapter.updater.daemon = False
    adapter.updater.start()
    configure_scheduler(adapter.config, adapter)
    load_plugins(adapter.config, adapter)
    if adapter.scheduler_available:
        adapter.scheduler.start()
    bot_started.send(adapter)
