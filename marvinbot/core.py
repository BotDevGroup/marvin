from datetime import timedelta
from collections import defaultdict, OrderedDict
from marvinbot.cache import cache
from marvinbot.errors import HandlerException
from telegram.error import NetworkError, Unauthorized
import telegram
import logging

log = logging.getLogger(__name__)
PERIODIC_TASKS = OrderedDict()


_ADAPTER = None


def configure_adapter(config):
    global _ADAPTER
    _ADAPTER = TelegramAdapter(config)
    return _ADAPTER


def get_adapter():
    global _ADAPTER
    if _ADAPTER:
        return _ADAPTER


class TelegramAdapter(object):
    def __init__(self, config):
        token = config.get('telegram_token')
        self.config = config
        self.bot = telegram.Bot(token)
        self.handlers = defaultdict(list)

    def fetch_updates(self, last_update_id):
        for update in self.bot.getUpdates(offset=last_update_id, timeout=int(self.config.get('fetch_timeout', 5))):
            yield update

    def add_handler(self, handler, priority=0):
        log.info("Adding handler: {}, priority: {}".format(handler, priority))
        self.handlers[priority].append(handler)

    def process_update(self, update):
        log.info("Processing update: %s", update)
        for priority in sorted(self.handlers):
            for handler in self.handlers[priority]:
                if handler.can_handle(update):
                    try:
                        handler.process_update(update)
                        return
                    except HandlerException as e:
                        log.error(e)
                        raise e


def add_periodic_task(name, schedule, task, options=None, *args, **kwargs):
    """Register a periodic task.

    Schedule can be a python datetime.timedelta object or a celery crontab object."""
    PERIODIC_TASKS[name] = {
        'task': task,
        'schedule': schedule,
    }
    if args:
        PERIODIC_TASKS[name]['args'] = args
    if kwargs:
        PERIODIC_TASKS[name]['kwargs'] = kwargs
    if options:
        PERIODIC_TASKS[name]['options'] = options


def get_periodic_tasks(config):
    """Returns a list of periodic tasks in a format Celerybeat understands.

    This includes both built-in tasks and any tasks that might have been added by
    plugins by calling `add_periodic_task`.
    """
    # Default built-in tasks
    tasks = {}

    if PERIODIC_TASKS:
        tasks.update(dict(PERIODIC_TASKS))
    return tasks
