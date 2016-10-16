from marvinbot.defaults import DEFAULT_PRIORITY
from marvinbot.errors import PluginLoadException
from marvinbot.signals import plugin_loaded
import importlib
import logging

log = logging.getLogger(__name__)


__all__ = ['load_module', 'load_plugins', 'Plugin']


def load_module(modspec, config, adapter):
    enabled = config.pop('enabled', True)
    short_name = config.get('short_name')
    mod = importlib.import_module(modspec)
    if hasattr(mod, 'plugin'):
        plugin = mod.plugin
    else:
        plugin = Plugin(short_name, modspec, adapter)

    if short_name:
        plugin.name = short_name
    plugin.config = config
    plugin.adapter = adapter
    plugin.enabled = enabled
    plugin.modspec = modspec

    adapter.add_plugin(plugin)
    plugin.load()

    return plugin


def load_plugins(config, adapter):
    modules_to_load = config.get("plugins")
    plugin_configs = config.get("plugin_configuration", {})

    if modules_to_load:
        for module in modules_to_load:
            if module:
                # Pass along module specific configuration, if available
                try:
                    plugin = load_module(module, plugin_configs.get(module, {}), adapter)
                    plugin_loaded.send(plugin)
                except Exception as e:
                    # Report the error, continue loading the other plugins
                    log.warn("Plugin [{}] not loaded due to an error".format(module))
                    log.exception(e)


class Plugin(object):
    """An object representing a bot plugin"""
    def __init__(self, name, enabled=True, config=None):
        if not name:
            raise ValueError('Name is required')
        self.name = name

        # These will get filled in by the plugin loader later
        self.config = config
        self.modspec = None
        self.adapter = None
        self.enabled = enabled

    def get_default_config(self):
        """Returns a dict with the default config for the plugin.

        Subclasses can override this method to provide different defaults"""
        return {
            'short_name': self.name,
            'enabled': True
        }

    def get_config(self):
        config = self.get_default_config()
        config.update(self.config)

        return config

    def _do_configure(self):
        config = self.get_config()
        try:
            self.configure(config)
            mod = importlib.import_module(self.modspec)
            if hasattr(mod, 'configure'):
                # Call module-level configure method, passing it's module specific config
                log.info('[%s] Calling configure() for module [%s]', self.name, self.modspec)
                mod.configure(self.config)
        except Exception as e:
            raise PluginLoadException from e

    def configure(self, config):
        """Configure this plugin, given an optional config"""
        pass

    def _do_load_models(self):
        try:
            log.info('[%s] Attempting to import models', self.name)
            models_mod = importlib.import_module(self.modspec + ".models")
        except Exception as e:
            log.warn('[%s] No models loaded for [%s]', self.name, self.module)
            log.exception(e)

    def _do_setup_handlers(self):
        try:
            log.info('[%s] Attempting to import handlers for module [%s]', self.name, self.module)
            self.setup_handlers(self.adapter)

            tasks_mod = importlib.import_module(self.modspec + ".tasks")
            if hasattr(tasks_mod, 'setup'):
                tasks_mod.setup(self.adapter)
        except Exception as e:
            # Module has no tasks, ignore
            log.warn('[%s] No handlers loaded for [%s]', self.name, self.module)
            log.exception(e)

    def setup_handlers(self, adapter):
        """Override this to setup handlers directly from this plugin"""
        pass

    def load(self):
        log.info("Loading plugin [%s]", self.name)
        if not self.adapter:
            raise ValueError('An adapter is required')
        if not self.modspec:
            raise ValueError('Modspec is required')
        self.module = importlib.import_module(self.modspec)
        self._do_configure()
        self._do_load_models()
        self._do_setup_handlers()

    def add_handler(self, handler, priority=DEFAULT_PRIORITY):
        self.adapter.add_handler(handler, priority=priority, plugin=self)

    def __str__(self):
        return "{name}".format(name=self.modspec)
