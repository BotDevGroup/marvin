from marvinbot.utils import localized_date
from telegram.error import NetworkError, Unauthorized
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import threading
import polling
import logging
import time


log = logging.getLogger(__name__)


class PollingThread(threading.Thread):
    def __init__(self, func, process_func, checker=None, poll_interval=60, poll_timeout=30,
                 ignored_exceptions=None, send_last_update_time=False, send_last_result=False,
                 hard_timeout=False, thread_name=None, workers=None, *args, **kwargs):
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

        # Create an executor or not if no workers
        if workers:

            self.executor = ThreadPoolExecutor(max_workers=int(workers))
            log.info('Starting with a ThreadPoolExecutor, workers=%d', workers)
        else:
            log.info('Executing processes inline, no workers')
            self.executor = None

    def do_poll(self, cur_interval=None):
        if not cur_interval:
            cur_interval = self.poll_interval
        return polling.poll(partial(self.func, *self.func_args, **self.func_kwargs),
                            check_success=self.checker, ignore_exceptions=self.ignored_exceptions,
                            timeout=self.poll_timeout, step=cur_interval)

    def execute(self, func, *args, **kwargs):
        if self.executor:
            return self.executor.submit(func, *args, **kwargs), True
        else:
            return func(*args, **kwargs), False

    def run(self):
        self.running = True
        log.info("Starting polling thread")

        cur_interval = self.poll_interval
        while self.running:
            try:
                result = self.do_poll(cur_interval)
                process_result, is_async = self.execute(self.process_func, result)
                if self.send_last_result:
                    # This makes the process synchronous
                    self.update_last_result(process_result, is_async)
                if self.send_last_update_time:
                    self.func_kwargs['last_update_time'] = localized_date()
                cur_interval = self.poll_interval
            except polling.TimeoutException:
                # If true, abort immediately
                if self.hard_timeout:
                    self.running = False
                # log.debug("Timeout triggered")
            except Exception as e:
                # Log the error, but keep polling
                log.error("Error ocurred (polling every %f seconds now): %s", cur_interval, str(e))
                # Temporarily increase the polling interval on errors
                cur_interval = self.adjust_interval(cur_interval)
            time.sleep(cur_interval)

    @staticmethod
    def adjust_interval(cur_interval):
        if cur_interval == 0:
            cur_interval = 1
        elif cur_interval < 30:
            cur_interval += cur_interval / 2
        elif cur_interval > 30:
            cur_interval = 30
        return cur_interval

    def update_last_result(self, value, is_async=True):
        self.func_kwargs['last_result'] = value.result() if is_async else value

    def stop(self):
        """Shut down everything in an orderly fashion"""
        self.running = False
        if self.executor:
            self.executor.shutdown()


UPDATER_DEFAULTS = {
            'polling_interval': 0.5,
            'polling_expiry': 10,
            'polling_workers': 5,
        }


class TelegramPollingThread(PollingThread):
    def __init__(self, adapter, workers=UPDATER_DEFAULTS.get('polling_workers')):
        self.adapter = adapter
        updater_config = UPDATER_DEFAULTS
        updater_config.update(self.adapter.config.get('updater', {}))

        # If specified on the constructor, override the config
        updater_config['polling_workers'] = workers or updater_config['polling_workers']
        super(TelegramPollingThread, self).__init__(self.fetch_updates, self.on_update,
                                                    checker=lambda x: bool(x),
                                                    ignored_exceptions=[NetworkError, Unauthorized],
                                                    send_last_result=True, send_last_update_time=True,
                                                    poll_interval=updater_config.get('polling_interval'),
                                                    poll_timeout=updater_config.get('polling_expiry'),
                                                    thread_name='telegram-polling-thread',
                                                    workers=updater_config.get('polling_workers'))

    def fetch_updates(self, last_result=None, last_update_time=None):
        # Fetch a list of Telegram updates for the bot, passing in the last_update_id
        # as stored in last_result
        updates = list(self.adapter.fetch_updates(last_result))
        return updates

    def on_update(self, updates):
        last_update = None
        for update in updates:
            # Execute the actual processing asynchronously
            self.execute(self.adapter.process_update, update)
            last_update = update
        if last_update:
            # This is needed so we can avoid pulling the same update twice
            # Telegram's API returns the latest update after this ID
            return last_update.update_id + 1
