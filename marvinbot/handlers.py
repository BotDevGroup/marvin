from celery import Task
from telegram.ext.messagehandler import Filters
import telegram


class Handler(object):
    def __init__(self, callback, allow_edits=True, call_async=True):
        self.callback = callback
        if not self.callback:
            raise ValueError('Callback is required')
        self.allow_edits = allow_edits
        self.call_async = call_async

    def get_message(self, update):
        if (isinstance(update, telegram.Update) and (update.message or update.edited_message and self.allow_edited)):
            message = update.message or update.edited_message
            return message

    def can_handle(self, update):
        """Return True/False if this handler can process the given update."""
        raise NotImplementedError

    def process_update(self, update):
        """Process the given update.

        Callbacks are expected to get a hold of the adapter (it's a singleton)."""
        raise NotImplementedError

    def do_call(self, update, *args, **kwargs):
        if self.call_async and isinstance(self.callback, Task):
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

    def process_update(self, update):
        message = self.get_message(update)
        params = message.text.split(' ')[1:]
        self.do_call(update, *params)

    def __str__(self):
        return self.command


class MessageHandler(Handler):
    def __init__(self, filters, callback, strict=False, *args, **kwargs):
        """Handler that responds to messages based on whether they match filters.

        Params:
        `strict`: If True, message must match ALL filters."""
        if not filters:
            raise ValueError('At least one filter is required')

        if isinstance(filters, list):
            self.filters = filters
        else:
            self.filters = [filters]
        self.strict = True
        super(MessageHandler, self).__init__(callback, *args, **kwargs)

    def can_handle(self, update):
        message = self.get_message(update)

        if self.strict:
            return all(f(message) for f in self.filters)
        else:
            return any(f(message) for f in self.filters)

    def process_update(self, update):
        self.do_call(update)

    def __str__(self):
        return self.command
