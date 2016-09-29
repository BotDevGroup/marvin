from __future__ import absolute_import
from celery import Celery
from celery.signals import worker_init, worker_shutdown
from marvinbot.utils import get_config, load_sources, configure_mongoengine
from marvinbot.core import get_adapter, get_periodic_tasks
from marvinbot.cache import configure_cache
from kombu import Exchange, Queue


adapter_generator = None


def initialize():
    global adapter_generator
    config = get_config()
    adapter_generator = get_adapter(config)
    configure_cache(config)
    configure_mongoengine(config)
    load_sources(config, adapter_generator())


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

    initialize()

    return celery

celery = marvinbot_app = configure()


@worker_init.connect
def setup_modules(signal, sender):
    initialize()


# @worker_shutdown.connect
# def on_shutdown(signal, sender):
#     adapter.stop()
