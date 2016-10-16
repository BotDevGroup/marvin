#!/usr/bin/env ipython

import os
import readline
from pprint import pprint

from marvinbot.log import configure_logging
from marvinbot import *
from marvinbot.models import *
from marvinbot.plugins import load_plugins
from marvinbot.utils import get_config, configure_mongoengine
from marvinbot.cache import configure_cache
import logging

os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
configure_logging(config)
configure_mongoengine(config)
configure_cache(config)

from marvinbot.core import get_adapter, configure_adapter
configure_adapter(config)
adapter = get_adapter()
from marvinbot.tasks import *
from marvinbot.net import *
configure_downloader(config)
load_plugins(config, adapter)
