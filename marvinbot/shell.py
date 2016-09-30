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


os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
configure_mongoengine(config)
configure_cache(config)
configure_adapter(config)
load_sources(config)
adapter = get_adapter()
