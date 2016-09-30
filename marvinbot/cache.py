from marvinbot.cache_impl import configure_cache
from marvinbot.utils import get_config


def get_cache_config():
    config = get_config()

    return config

cache = configure_cache(get_cache_config())
