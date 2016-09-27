#!/usr/bin/env ipython

import os
import readline
from pprint import pprint

from marvinbot import *
from marvinbot.models import *
from marvinbot.utils import get_config, load_sources


os.environ['PYTHONINSPECT'] = 'True'
config = get_config()
load_sources(config)
