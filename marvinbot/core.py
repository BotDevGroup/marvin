from collections import defaultdict, OrderedDict
from marvinbot.errors import HandlerException
from marvinbot.defaults import DEFAULT_PRIORITY
from marvinbot.models import User
from marvinbot.plugins import Plugin
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
        self.plugin_registry = {}
        self.bot_info = self.bot.getMe()

    def fetch_updates(self, last_update_id=None):
        for update in self.bot.getUpdates(offset=last_update_id, timeout=int(self.config.get('fetch_timeout', 5))):
            yield update

    def add_handler(self, handler, priority=DEFAULT_PRIORITY, plugin=None):
        if not plugin:
            plugin = self.plugin_for_handler(handler)
        handler.plugin = plugin

        log.info("Adding handler: {}, priority: {}, plugin: {}".format(handler, priority, plugin))
        self.handlers[priority].append(handler)

    def plugin_for_handler(self, handler):
        mod = handler.callback.__module__.split('.', 1)[0]
        plugins = self.plugins_by_modspec()
        if mod in plugins:
            return plugins[mod]

    def plugins_by_modspec(self):
        return {p.modspec: p for p in self.plugin_registry.values()}

    def process_update(self, update):
        log.info("Processing update: %s", update)
        for priority in sorted(self.handlers):
            for handler in self.handlers[priority]:
                log.debug('Trying handler: ', handler)
                if handler.plugin and not handler.plugin.enabled:
                    continue
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

    def add_plugin(self, plugin):
        if not isinstance(plugin, Plugin):
            raise ValueError('plugin must be a Plugin sublass')
        self.plugin_registry[plugin.name] = plugin

    def enable_plugin(self, plugin_name, enable=True):
        if plugin_name in self.plugin_registry:
            self.plugin_registry[plugin_name].enabled = enable

    def plugin_definition(self, plugin_name):
        return self.plugin_registry.get(plugin_name)

    def commands(self, exclude_internal=False):
        from marvinbot.handlers import CommandHandler
        result = OrderedDict()
        for priority, handlers in self.handlers.items():
            if exclude_internal and priority == 0:
                continue
            for handler in handlers:
                if exclude_internal and handler.plugin is None:
                    continue
                if isinstance(handler, CommandHandler):
                    result[handler.command] = handler
        return result


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
