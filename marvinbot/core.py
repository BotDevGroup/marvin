from celery import Task
from datetime import timedelta
from collections import defaultdict
from marvinbot.errors import HandlerException
import telegram
import logging

log = logging.getLogger(__name__)


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
            handler = CommandHandler(command_name, func, self)
            self.add_handler(handler)
        return command_decorator


class Handler(object):
    def __init__(self, callback, allow_edits=True):
        self.callback = callback
        self.allow_edits = allow_edits

    def get_message(self, update):
        if (isinstance(update, telegram.Update) and (update.message or update.edited_message and self.allow_edited)):
            message = update.message or update.edited_message
            return message

    def can_handle(self, update):
        """Return True/False if this handler can process the given update."""
        raise NotImplementedError

    def process_update(self, update, call_async=True):
        """Process the given update.

        Callbacks are expected to get a hold of the adapter (it's a singleton)."""
        raise NotImplementedError

    def do_call(self, update, call_async=True, *args, **kwargs):
        if call_async and isinstance(self.callback, Task):
            self.callback.s(update, *args, **kwargs).apply_async()
        else:
            self.callback(update, *args, **kwargs)


class CommandHandler(Handler):
    def __init__(self, command, callback, *args, **kwargs):
        self.command = command
        super(CommandHandler, self).__init__(callback, *args, **kwargs)

    def can_handle(self, update):
        message = self.get_message(update)

        return (message.text and message.text.startswith('/')
                and message.text[1:].split(' ')[0].split('@')[0] == self.command)

    def process_update(self, update, call_async=True):
        message = self.get_message(update)
        params = message.text.split(' ')[1:]
        self.do_call(update, *params)

    def __str__(self):
        return self.command


def get_periodic_tasks(config):
    return {
        'fetch_messages': {
            'task': 'marvinbot.tasks.fetch_messages',
            'schedule': timedelta(seconds=5),
            'options': {
                'expires': 5  # If it takes longer than this to execute, expire and wait for the next
            }
        },
    }
