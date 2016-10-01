from marvinbot.utils import localized_date
from telegram.error import NetworkError, Unauthorized
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import threading
import polling
import logging


log = logging.getLogger(__name__)


class PollingThread(threading.Thread):
    def __init__(self, func, process_func, checker=None, poll_interval=60, poll_timeout=30,
                 ignored_exceptions=None, send_last_update_time=False, send_last_result=False,
                 hard_timeout=False, thread_name=None, workers=2, *args, **kwargs):
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
        - `workers`: max amount of threads to execute `process_func`
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

        # Make daemonic by default, so program exits if this is the last thread
        self.daemon = True
        self.executor = ThreadPoolExecutor(max_workers=workers)

    def do_poll(self):
        return polling.poll(partial(self.func, *self.func_args, **self.func_kwargs),
                            check_success=self.checker, ignore_exceptions=self.ignored_exceptions,
                            timeout=self.poll_timeout, step=self.poll_interval)

    def run(self):
        self.running = True
        log.info("Starting polling thread")

        while self.running:
            try:
                result = self.do_poll()
                process_result = self.executor.submit(self.process_func, result)
                if self.send_last_result:
                    # This makes the process synchronous
                    self.update_last_result(process_result)
                if self.send_last_update_time:
                    self.func_kwargs['last_update_time'] = localized_date()
            except polling.TimeoutException:
                # If true, abort immediately
                if self.hard_timeout:
                    self.running = False
                log.debug("Timeout triggered")
                continue
            except Exception as e:
                # Log the error, but keep polling
                log.error("Error ocurred: %s", str(e))

    def update_last_result(self, future):
        self.func_kwargs['last_result'] = future.result()

    def stop(self):
        """Shut down everything in an orderly fashion"""
        self.running = False
        self.executor.shutdown()


UPDATER_DEFAULTS = {
            'polling_interval': 0.5,
            'polling_expiry': 10,
            'polling_workers': 2,
        }


class TelegramPollingThread(PollingThread):
    def __init__(self, adapter):
        self.adapter = adapter
        updater_config = UPDATER_DEFAULTS
        updater_config.update(self.adapter.config.get('updater', {}))

        super(TelegramPollingThread, self).__init__(self.fetch_updates, self.on_update,
                                                    checker=lambda x: bool(x),
                                                    ignored_exceptions=[NetworkError, Unauthorized],
                                                    send_last_result=True, send_last_update_time=True,
                                                    poll_interval=updater_config.get('polling_interval'),
                                                    poll_timeout=updater_config.get('polling_expiry'),
                                                    thread_name='telegram-polling-thread',
                                                    workers=updater_config.get('polling_workers', 2))

    def fetch_updates(self, last_result=None, last_update_time=None):
        # Fetch a list of Telegram updates for the bot, passing in the last_update_id
        # as stored in last_result
        updates = list(self.adapter.fetch_updates(last_result))
        return updates

    def on_update(self, updates):
        last_update = None
        for update in updates:
            # Execute the actual processing asynchronously
            self.executor.submit(self.adapter.process_update, update)
            last_update = update
        if last_update:
            # This is needed so we can avoid pulling the same update twice
            # Telegram's API returns the latest update after this ID
            return last_update.update_id + 1
