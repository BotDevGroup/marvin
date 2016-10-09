from marvinbot.errors import DownloadException
from marvinbot.utils import localized_date
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import requests
import os


DOWNLOADER_DEFAULTS = {
    "download_path": os.path.abspath("var/files"),
    "workers": 2
}

DOWNLOAD_PATH = DOWNLOADER_DEFAULTS.get('download_path')
WORKERS = None

METHOD_MAP = {
    'get': requests.get,
    'post': requests.post,
}


log = logging.getLogger(__name__)


__all__ = ['fetch_from_telegram', 'download_file', 'configure_downloader']


def fetch_from_telegram(adapter, file_id, target_filename=None, on_done=None, file_prefix='telegram'):
    target = target_filename or file_id
    target = make_path(file_prefix, target)
    if os.path.exists(target):
        # Already got it
        if on_done:
            on_done(target)
        log.info("%s already exists, returning existing copy", target)
        return target, False
    telegram_file = adapter.bot.getFile(file_id)
    future, is_async = execute_async(on_done, save_from_telegram, telegram_file, target)
    return target, is_async


def save_from_telegram(telegram_file, target):
    try:
        telegram_file.download(target)
        return target
    except Exception as e:
        log.error(e)
        raise DownloadException from e


def download_file(url, method='get', target_filename=None, file_prefix=None,
                  on_done=None, chunk_size=2048, **params):
    target = target_filename or os.path.basename(url)
    filename = make_path(file_prefix, target)

    if os.path.exists(filename):
        # Already got it
        if on_done:
            on_done(filename)
        log.info("%s already exists, returning existing copy", filename)
        return filename, False
    r = partial(METHOD_MAP.get(method), url, **params)
    future, is_async = execute_async(on_done, save_from_request, filename, r, chunk_size)
    return filename, is_async


def save_from_request(filename, fetcher, chunk_size):
    try:
        request = fetcher()
        with open(filename, 'wb') as fd:
            for chunk in request.iter_content(chunk_size):
                fd.write(chunk)
        return filename
    except Exception as e:
        log.error(e)
        raise DownloadException from e


def make_path(prefix, *args):
    if not prefix:
        prefix = ''
    if callable(prefix):
        prefix = prefix()
    path = os.path.join(DOWNLOAD_PATH, prefix, *args)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return os.path.abspath(path)


def execute_async(on_done, func, *args, **kwargs):
    if WORKERS:
        future = WORKERS.submit(func, *args, **kwargs)
        if on_done:
            future.add_done_callback(lambda x: on_done(x.result()))
        return future, True
    else:
        result = func(*args, **kwargs)
        return on_done(result) if on_done else result, False


def configure_downloader(config):
    global DOWNLOAD_PATH, WORKERS

    dconfig = {}
    dconfig.update(DOWNLOADER_DEFAULTS)
    dconfig.update(config.get('downloader', {}))

    DOWNLOAD_PATH = dconfig.get('download_path')
    # Create an executor or not if no workers
    workers = dconfig.get('workers')
    if workers:
        WORKERS = ThreadPoolExecutor(max_workers=int(workers))
        log.info('Starting Downloader with a ThreadPoolExecutor, workers=%d', workers)
    else:
        log.info('Executing Downloader jobs inline, no workers')
        WORKERS = None
