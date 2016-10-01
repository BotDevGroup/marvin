#!/usr/bin/env ipython

import os
import readline
from pprint import pprint

from marvinbot import *
from marvinbot.models import *
from marvinbot.utils import get_config, load_sources, configure_mongoengine
from marvinbot.core import get_adapter, configure_adapter
from marvinbot.tasks import *
from marvinbot.cache import configure_cache
import logging

LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger('bot-shell')


os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
configure_mongoengine(config)
configure_cache(config)
configure_adapter(config)
adapter = get_adapter()
load_sources(config, adapter)
