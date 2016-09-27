from datetime import datetime
from dateutil.tz import tzlocal
import pytz
import importlib
import os
import json


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


def get_config(config_file=None):
    """
    Gets a configuration object for marvinbot.

    Tries to get the config specified for an environment variable named MARVINBOT_CONFIG. If not found, tries to fetch
    the configuration from a path relative to the marvinbot module. If none of that is successful, tries to load it
    from the current working directory.
    """
    if not config_file:
        config_file = os.environ.get('MARVINBOT_CONFIG') or get_from_module('marvinbot',
                                                                            'settings.json', 'default_settings.json')

    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        raise ValueError('ConfigFile [{}] not found'.format(config_file))

    return config


def load_module(modspec, config):
    mod = importlib.import_module(modspec)
    if hasattr(mod, 'configure'):
        # Call module-level configure method
        mod.configure(config)

    try:
        # If successful, tasks will already be registered with Celery
        mod = importlib.import_module(modspec + ".tasks")
    except Exception:
        # Module has no tasks, ignore
        pass


CONFIG = get_config()
DEFAULT_TIMEZONE = os.environ.get('TZ', CONFIG.get('default_timezone'))
TZ = pytz.timezone(DEFAULT_TIMEZONE)


def load_sources(config):
    modules_to_load = config.get("plugins")

    if modules_to_load:
        for module in modules_to_load:
            if module:
                # Pass along module specific configuration, if available
                load_module(module, config.get(module, {}))


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
