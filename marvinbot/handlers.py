from celery import Task
from telegram.ext.messagehandler import Filters
from marvinbot.models import User
from marvinbot.utils import get_message
from marvinbot.core import get_adapter
from datetime import datetime
import logging


log = logging.getLogger(__name__)


class Handler(object):
    def __init__(self, callback, adapter=None, allow_edits=True, call_async=False, discard_threshold=300):
        """Initialize this handler.

        Parameters:
        - `allow_edits`: if enabled, handler will also accept edits.
        - `call_async`: if callback is a celery task, call asynchronously.
          Else call in the current worker.
        - `discard_threshold`: Messages older than X seconds will get discarded.
        '"""
        self.callback = callback
        if not self.callback:
            raise ValueError('Callback is required')
        self.allow_edits = allow_edits
        self.call_async = call_async
        self.discard_threshold = discard_threshold
        self.adapter = adapter or get_adapter()

    def get_registered_user(self, message):
        """Return a registered User instance for message.

        Returns None if the user isn't registered."""
        user = message.from_user
        user_id = user.id

        return User.by_id(user_id)

    def can_handle(self, update):
        """Return True/False if this handler can process the given update."""
        message = get_message(update, self.allow_edits)
        age = datetime.now() - message.date
        if self.discard_threshold and age.total_seconds() > self.discard_threshold:
            return False

        return self.validate(message)

    def validate(self, message):
        """Return True/False if this handler can process the given update.

        You need to override this method."""
        raise NotImplementedError

    def process_update(self, update, *args, **kwargs):
        """Process the given update.

        Callbacks are expected to get a hold of the adapter (it's a singleton).
        Override if you need to do anything other than calling the callback and then
        call the parent class method."""
        self.do_call(update, *args, **kwargs)

    def do_call(self, update, *args, **kwargs):
        if self.call_async and isinstance(self.callback, Task) and self.adapter.async_available:
            self.callback.s(update, *args, **kwargs).apply_async()
        else:
            self.callback(update, *args, **kwargs)


class CommandHandler(Handler):
    def __init__(self, command, callback, required_roles=None, *args, **kwargs):
        self.command = command
        self.required_roles = None
        if required_roles:
            if not isinstance(required_roles, list):
                self.required_roles = [required_roles]
            else:
                self.required_roles = required_roles
        super(CommandHandler, self).__init__(callback, *args, **kwargs)

    def validate(self, message):
        if self.required_roles:
            user = self.get_registered_user(message)
            if not user:
                return False
            if user.role not in self.required_roles:
                return False

        return (message.text and message.text.startswith('/')
                and message.text[1:].split(' ')[0].split('@')[0] == self.command)

    def process_update(self, update):
        message = get_message(update, self.allow_edits)
        params = message.text.split(' ')[1:]

        super(CommandHandler, self).process_update(update, *params)

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

    def validate(self, message):
        if self.strict:
            return all(f(message) for f in self.filters)
        else:
            return any(f(message) for f in self.filters)

    def __str__(self):
        return str(self.filters)
