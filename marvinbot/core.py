from collections import defaultdict, OrderedDict
from marvinbot.errors import HandlerException
from marvinbot.models import User
import telegram
import logging
import importlib
import traceback

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
        self.async_available = False

    def fetch_updates(self, last_update_id=None):
        for update in self.bot.getUpdates(offset=last_update_id, timeout=int(self.config.get('fetch_timeout', 5))):
            yield update

    def add_handler(self, handler, priority=2):
        log.info("Adding handler: {}, priority: {}".format(handler, priority))
        self.handlers[priority].append(handler)

    def process_update(self, update):
        log.info("Processing update: %s", update)
        for priority in sorted(self.handlers):
            for handler in self.handlers[priority]:
                log.debug('Trying handler: ', handler)
                if handler.can_handle(update):
                    log.debug('Using handler: ', handler)
                    try:
                        handler.process_update(update)
                        return
                    except Exception as e:
                        log.exception(e)
                        # self.notify_owners(r"⚠ Handler Error: ```{}```".format(traceback.format_exc()))
                        raise HandlerException from e

    def notify_owners(self, message, parse_mode='Markdown'):
        owners = User.objects.filter(role='owner')
        for owner in owners:
            self.bot.sendMessage(owner.id, message, parse_mode=parse_mode)


# TODO(wcx): Implement an alternate scheduler
# def add_periodic_task(name, schedule, task, options=None, *args, **kwargs):
#     """Register a periodic task.

#     Schedule can be a python datetime.timedelta  crontab object."""
#     PERIODIC_TASKS[name] = {
#         'task': task,
#         'schedule': schedule,
#     }
#     if args:
#         PERIODIC_TASKS[name]['args'] = args
#     if kwargs:
#         PERIODIC_TASKS[name]['kwargs'] = kwargs
#     if options:
#         PERIODIC_TASKS[name]['options'] = options


# def get_periodic_tasks(config):
#     """Returns a list of periodic tasks in a format Celerybeat understands.

#     This includes both built-in tasks and any tasks that might have been added by
#     plugins by calling `add_periodic_task`.
#     """
#     # Default built-in tasks
#     tasks = {}

#     if PERIODIC_TASKS:
#         tasks.update(dict(PERIODIC_TASKS))
#     return tasks


def load_module(modspec, config, adapter):
    try:
        mod = importlib.import_module(modspec)
        if hasattr(mod, 'configure'):
            # Call module-level configure method, passing it's module specific config
            log.info('Calling configure() for module [%s]', mod)
            mod.configure(config)
    except Exception as e:
        log.warn("Plugin [{}] not loaded due to an error".format(modspec))
        log.exception(e)
        return

    try:
        log.info('Attempting to import models for module [%s]', mod)
        models_mod = importlib.import_module(modspec + ".models")
    except Exception as e:
        log.warn('No models loaded for [%s]: %s', mod, e)
        log.exception(e)

    try:
        # If successful, tasks will already be registered with Celery
        log.info('Attempting to import tasks for module [%s]', mod)
        tasks_mod = importlib.import_module(modspec + ".tasks")
        if hasattr(tasks_mod, 'setup'):
            tasks_mod.setup(adapter)
    except Exception as e:
        # Module has no tasks, ignore
        log.warn('No tasks loaded for [%s]', mod)
        log.exception(e)


def load_sources(config, adapter):
    modules_to_load = config.get("plugins")
    plugin_configs = config.get("plugin_configuration", {})

    if modules_to_load:
        for module in modules_to_load:
            if module:
                # Pass along module specific configuration, if available
                load_module(module, plugin_configs.get(module, {}), adapter)
