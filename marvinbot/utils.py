from mongoengine import connect as mongoengine_connect
from pymongo import ReadPreference
from datetime import datetime
from dateutil.tz import tzlocal
import telegram
import pytz
import importlib
import os
import json
import sys
import logging
import logging.config

log = logging.getLogger(__name__)


def get_from_module(modspec, fspec, default=None):
    """
    Imports module specified by modspec, and returns fspec relative to it.

    If the resulting file doesn't exist, returns default.
    """
    mod = importlib.import_module(modspec)
    mod_path = os.path.dirname(mod.__file__)

    file_path = os.path.join(mod_path, fspec)
    if os.path.exists(file_path):
        return file_path
    else:
        return default


DEFAULT_CONFIG = 'default_settings.json'


def get_config(config_file=None):
    """
    Gets a configuration object for marvinbot.

    Tries to get the config specified for an environment variable named MARVINBOT_CONFIG. If not found, tries to fetch
    the configuration from a path relative to the marvinbot module. If none of that is successful, tries to load it
    from the current working directory.
    """
    config = {}
    if os.path.exists(DEFAULT_CONFIG):
        with open(DEFAULT_CONFIG, 'r') as f:
            config.update(json.load(f))

    if not config_file:
        config_file = os.environ.get('MARVINBOT_CONFIG') or 'settings.json'

    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config.update(json.load(f))

    else:
        raise ValueError('ConfigFile [{}] not found'.format(config_file))

    return config


def configure_logging(config):
    options = config.get('logging', {})
    logging.config.dictConfig(options)


def configure_mongoengine(config):
    if isinstance(config, dict):
        host = config.get("mongodb.host", "localhost")
        port = config.get("mongodb.port", 27017)
        username = config.get("mongodb.username") or None
        password = config.get("mongodb.password") or None
        db_name = config.get("mongodb.db_name", "marvinbot")

    params = {
        'host': host,
        'port': int(port),
    }

    if username:
        params['username'] = username
    if password:
        params['password'] = password

    mongoengine_connect(db_name, tz_aware=True, read_preference=ReadPreference.PRIMARY_PREFERRED, connect=False, **params)


def load_module(modspec, config, adapter):
    try:
        mod = importlib.import_module(modspec)
        if hasattr(mod, 'configure'):
            # Call module-level configure method, passing it's module specific config
            log.info('Calling configure() for module [%s]', mod)
            mod.configure(config)
    except Exception as e:
        log.warn("Plugin {} not loaded due to an error: {}".format(modspec, str(e)))
        return

    try:
        log.info('Attempting to import models for module [%s]', mod)
        models_mod = importlib.import_module(modspec + ".models")
    except Exception:
        log.warn('No models loaded for [%s]', mod)

    try:
        # If successful, tasks will already be registered with Celery
        log.info('Attempting to import tasks for module [%s]', mod)
        tasks_mod = importlib.import_module(modspec + ".tasks")
        if hasattr(tasks_mod, 'setup'):
            tasks_mod.setup(adapter)
    except Exception:
        # Module has no tasks, ignore
        log.warn('No tasks loaded for [%s]', mod)


CONFIG = get_config()
DEFAULT_TIMEZONE = os.environ.get('TZ', CONFIG.get('default_timezone'))
TZ = pytz.timezone(DEFAULT_TIMEZONE)


def load_sources(config, adapter):
    modules_to_load = config.get("plugins")

    if modules_to_load:
        for module in modules_to_load:
            if module:
                # Pass along module specific configuration, if available
                load_module(module, config.get(module, {}), adapter)


def localized_date(date=None, timezone=None):
    """
    Returns the given date, localized to the default timezone.

    If no date is given, return the localized current date.

    timezone should be a valid timezone object obtained via pytz.
    """
    if not timezone:
        timezone = TZ

    if not date:
        date = pytz.utc.localize(datetime.utcnow())
    if not date.tzinfo:
        # Attempt to guezz current server timezone
        # Should be ok for any date coming fom a naive call to datetime.now()
        date = date.replace(tzinfo=tzlocal())

    return date.astimezone(timezone)


def get_message(update, allow_edited=True):
    """Given an update, return the message portion of it.

    If the message is an edit, return the original if `allow_edited` is False. Else, returns the edited version.
    """
    if (isinstance(update, telegram.Update) and (update.message or update.edited_message and allow_edited)):
        message = update.message or update.edited_message
        return message
    return update.message
