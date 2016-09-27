from celery import Celery
from celery.signals import worker_init
from marvinbot.utils import get_config, load_sources
from kombu import Exchange, Queue


def configure_celery(section='celery'):
    config = get_config()

    celery = Celery('marvinbot',
                    broker=config.get('broker'),
                    backend=config.get('backend'),
                    include=['marvinbot.tasks'])

    load_sources(config)

    # Optional configuration, see the application user guide.
    celery.conf.update(
        CELERY_TASK_RESULT_EXPIRES=3600,
        CELERY_TIMEZONE=config.get('default_timezone'),
        CELERY_DEFAULT_QUEUE='marvinbot',
        CELERY_RESULT_BACKEND=config.get('backend'),
        CELERY_QUEUES=(
            Queue('marvinbot', Exchange('marvinbot'), routing_key='marvinbot'),
        ),
        # See: http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
        # CELERYBEAT_SCHEDULE=get_periodic_tasks()
    )

    return celery

celery = marvinbot_app = configure_celery()


if __name__ == '__main__':
    marvinbot_app.start()
