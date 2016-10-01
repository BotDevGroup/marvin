from marvinbot.utils import localized_date
from telegram.error import NetworkError, Unauthorized
from functools import partial
import threading
import polling
import logging


log = logging.getLogger(__name__)


class PollingThread(threading.Thread):
    def __init__(self, func, process_func, checker=None, poll_interval=60, poll_timeout=30,
                 ignored_exceptions=None, send_last_update_time=False, send_last_result=False,
                 hard_timeout=False, thread_name=None, *args, **kwargs):
        """Setup a Polling thread.

        Parameters:
        - `func`: function to call on each poll.
        - `process_func`: function that will process `func`s result when it arrives.
        - `checker`: (optional) function -> bool that given `func`'s result, determines if `process_func` will run.
        - `poll_interval`: Poll every X seconds, also accepts floats.
        - `poll_timeout`: Timeout after X seconds and retry the poll.
        - `ignored_exceptions`: List of exceptions that will be ignored during poll.
        - `send_last_update_time`: Send the last_update_time (last time the poller found something) to `func`.
        `func` should expect a parameter named `last_update_time`, which will be None on the first run.
        - `send_last_result`: Send the last result from `process_func` to `func` on the next run.
        `func` should expect a parameter named `last_result`, which will be None on the first run.
        - `hard_timeout`: Whether to exit on the first timeout.
        - `thread_name`: self explanatory
        - `*args`: positional parameters for `func`.
        - `**kwargs`: keyword parameters for `func`.
        """
        if not func:
            raise ValueError('function cannot be null')
        if not process_func:
            raise ValueError('process_func cannot be null')
        self.func = func
        self.process_func = process_func
        self.checker = checker
        self.ignored_exceptions = ignored_exceptions
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self.send_last_update_time = send_last_update_time
        self.send_last_result = send_last_result
        self.hard_timeout = hard_timeout
        self.func_args = args or ()
        self.func_kwargs = kwargs or {}

        self.running = False
        super(PollingThread, self).__init__()
        if thread_name:
            self.name = thread_name
        self.daemon = True

    def run(self):
        self.running = True
        log.info("Start polling thread")

        while self.running:
            try:
                result = polling.poll(partial(self.func, *self.func_args, **self.func_kwargs),
                                      check_success=self.checker, ignore_exceptions=self.ignored_exceptions,
                                      timeout=self.poll_timeout, step=self.poll_interval)
                if self.send_last_update_time:
                    self.func_kwargs['last_update_time'] = localized_date()
                process_result = self.process_func(result)
                if self.send_last_result:
                    self.func_kwargs['last_result'] = process_result
            except polling.TimeoutException:
                # If true, abort immediately
                if self.hard_timeout:
                    self.running = False
                log.debug("Timeout triggered")
                continue
            except Exception as e:
                log.error("Error ocurred: %s", str(e))

    def stop(self):
        self.running = False


class TelegramPollingThread(PollingThread):
    def __init__(self, adapter):
        self.adapter = adapter
        updater_config = self.adapter.config.get('updater', {
            'polling_interval': 0.5,
            'polling_expiry': 10,
        })
        super(TelegramPollingThread, self).__init__(self.fetch_updates, self.on_update,
                                                    checker=lambda x: bool(x),
                                                    ignored_exceptions=[NetworkError, Unauthorized],
                                                    send_last_result=True, send_last_update_time=True,
                                                    poll_interval=updater_config.get('polling_interval'),
                                                    poll_timeout=updater_config.get('polling_expiry'),
                                                    thread_name='telegram-polling-thread')

    def fetch_updates(self, last_result=None, last_update_time=None):
        updates = list(self.adapter.fetch_updates(last_result))
        return updates

    def on_update(self, updates):
        last_update = None
        for update in updates:
            self.adapter.process_update(update)
            last_update = update
        if last_update:
            return last_update.update_id + 1
