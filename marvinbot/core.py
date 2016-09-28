from datetime import timedelta
from collections import defaultdict, OrderedDict
from marvinbot.errors import HandlerException
from marvinbot.handlers import CommandHandler, MessageHandler
import telegram
import logging

log = logging.getLogger(__name__)
PERIODIC_TASKS = OrderedDict()


# Make a singleton
def get_adapter(config):
    adapter = None

    def make_adapter():
        adapter = TelegramAdapter(config.get('telegram_token'))
        return adapter

    def adapter_generator():
        if not adapter:
            return make_adapter()
        else:
            return adapter

    return adapter_generator


class TelegramAdapter(object):
    def __init__(self, token):
        self.bot = telegram.Bot(token)
        self.handlers = defaultdict(list)

    def fetch_updates(self, last_update_id):
        for update in self.bot.getUpdates(offset=last_update_id, timeout=10):
            yield update

    def add_handler(self, handler, priority=0):
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

    def register_command(self, command_name, **options):
        def command_decorator(func):
            handler = CommandHandler(command_name, func, **options)
            self.add_handler(handler)
        return command_decorator

    def register_message_handler(self, filters, **options):
        def message_decorator(func):
            handler = MessageHandler(filters, func, **options)
            self.add_handler(handler)
        return message_decorator


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
    tasks = {
        'fetch_messages': {
            'task': 'marvinbot.tasks.fetch_messages',
            'schedule': timedelta(seconds=5),
            'options': {
                'expires': 3  # If it takes longer than this to execute, expire and wait for the next
            }
        },
    }
    if PERIODIC_TASKS:
        tasks.update(dict(PERIODIC_TASKS))
    return tasks
