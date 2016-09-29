#!/usr/bin/env ipython

import os
import readline
from pprint import pprint

from marvinbot import *
from marvinbot.models import *
from marvinbot.utils import get_config, load_sources, configure_mongoengine
from marvinbot.core import get_adapter
from marvinbot.tasks import *
from marvinbot.cache import configure_cache


os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
adapter_generator = get_adapter(config)
adapter = adapter_generator()
configure_mongoengine(config)
configure_cache(config)
load_sources(config, adapter)
