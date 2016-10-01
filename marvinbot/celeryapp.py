from __future__ import absolute_import
from celery import Celery
from celery.signals import worker_init, worker_shutdown, celeryd_init
from marvinbot.utils import get_config, load_sources, configure_mongoengine
from marvinbot.core import configure_adapter, get_periodic_tasks, get_adapter
from marvinbot.cache import configure_cache
from marvinbot.signals import bot_started, bot_shutdown
from kombu import Exchange, Queue


def initialize(config):
    configure_cache(config)
    configure_mongoengine(config)
    configure_adapter(config)


def configure():
    config = get_config()

    celery = Celery('marvinbot',
                    broker=config.get('broker'),
                    backend=config.get('backend'),
                    include=['marvinbot.tasks'])

    # Optional configuration, see the application user guide.
    celery.conf.update(
        CELERY_TASK_RESULT_EXPIRES=3600,
        CELERY_TIMEZONE=config.get('default_timezone'),
        CELERY_DEFAULT_QUEUE='marvinbot',
        CELERY_RESULT_BACKEND=config.get('backend'),
        CELERY_ACCEPT_CONTENT=['json', 'pickle'],
        CELERY_TASK_SERIALIZER='pickle',
        CELERY_RESULT_SERIALIZER='json',

        CELERY_QUEUES=(
            Queue('marvinbot', Exchange('marvinbot'), routing_key='marvinbot'),
        ),
        # See: http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
        CELERYBEAT_SCHEDULE=get_periodic_tasks(config)
    )

    initialize(config)
    load_sources(config)

    return celery

celery = marvinbot_app = configure()


@worker_init.connect
def setup_modules(signal, sender):
    config = get_config()
    initialize(config)
    load_sources(config)


@celeryd_init.connect
def configure_marvinbot(sender=None, conf=None, **kwargs):
    if not sender.startswith('marvinbot_main'):
        return

    adapter = get_adapter()
    config = adapter.config
    updater_config = config.get('updater', {})
    if updater_config.get('mode', 'polling') != 'polling':
        return

    from marvinbot.polling import TelegramPollingThread

    adapter.updater_thread = TelegramPollingThread(adapter)
    adapter.updater_thread.start()
    bot_started.send(adapter)


@worker_shutdown.connect
def on_shutdown(signal, sender):
    adapter = get_adapter()
    bot_shutdown.send(adapter)
    if hasattr(adapter, 'updater_thread'):
        adapter.updater_thread.stop()
