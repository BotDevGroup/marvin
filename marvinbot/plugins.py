from flask import Blueprint
from marvinbot.defaults import DEFAULT_PRIORITY
from marvinbot.errors import PluginLoadException
from marvinbot.models import OAuthClientConfig, OAuthClientKey
from marvinbot.signals import plugin_loaded
import importlib
import logging
from urllib.parse import quote_plus


log = logging.getLogger(__name__)


__all__ = ['load_module', 'load_plugins', 'Plugin']


def load_module(modspec, config, adapter=None, webapp=None):
    enabled = config.pop('enabled', True)
    short_name = config.get('short_name')
    mod = importlib.import_module(modspec)
    if hasattr(mod, 'plugin'):
        plugin = mod.plugin
    else:
        plugin = Plugin(short_name, modspec, adapter)

    plugin.name = short_name or plugin.name or modspec
    plugin.config = config
    plugin.adapter = adapter
    plugin.enabled = enabled
    plugin.modspec = modspec

    if adapter:
        adapter.add_plugin(plugin)
    plugin.load()

    if webapp:
        web_interface = plugin.provide_blueprint(config)
        if web_interface:
            plugin_path = quote_plus(plugin.name)
            log.info(f"Mounting plugin [{plugin.name}] at path /plugins/{plugin_path}")
            webapp.register_blueprint(web_interface, url_prefix=f'/plugins/{plugin_path}')

    return plugin


def load_plugins(config, adapter=None, webapp=None):
    modules_to_load = config.get("plugins")
    plugin_configs = config.get("plugin_configuration", {})

    if modules_to_load:
        for module in modules_to_load:
            if module:
                # Pass along module specific configuration, if available
                try:
                    plugin = load_module(module, plugin_configs.get(module, {}), adapter, webapp)
                    plugin_loaded.send(plugin)
                except Exception as e:
                    # Report the error, continue loading the other plugins
                    log.warn("Plugin [{}] not loaded due to an error".format(module))
                    log.exception(e)


class Plugin(object):
    """An object representing a bot plugin"""
    def __init__(self, name=None, enabled=True, config=None):
        self.name = name

        # These will get filled in by the plugin loader later
        self.config = config
        self.modspec = None
        self.adapter = None
        self.enabled = enabled

    def get_default_config(self) -> dict:
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
        self.inhibit_schedules = config.get('inhibit_schedules', False)
        try:
            self.configure(config)
            mod = importlib.import_module(self.modspec)
            if hasattr(mod, 'configure'):
                # Call module-level configure method, passing it's module specific config
                log.info('[%s] Calling configure() for module [%s]', self.name, self.modspec)
                mod.configure(self.config)
            oauth_client_configs = self.config.get('oauth_clients', {})
            if oauth_client_configs:
                self.configure_oauth_from_config(oauth_client_configs)
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
            # Suppress these, as they are not helpful in case the plugin just doesn't have this.
            if "No module named" not in str(e):
                log.warn('[%s] No models loaded for [%s]', self.name, self.module)
                log.exception(e)

    def _do_setup_handlers(self):
        try:
            log.info('[%s] Attempting to import handlers for module [%s]', self.name, self.module)
            self.setup_handlers(self.adapter)
            if self.adapter.scheduler_available and not self.inhibit_schedules:
                self.setup_schedules(self.adapter)
            else:
                log.warn("[%s] Not loading schedules because inhibit_schedules==True", self.name)

            tasks_mod = importlib.import_module(self.modspec + ".tasks")
            if hasattr(tasks_mod, 'setup'):
                tasks_mod.setup(self.adapter)
            if self.adapter.scheduler_available and hasattr(tasks_mod, 'setup_schedules'):
                tasks_mod.setup_schedulers(self.adapter)
        except Exception as e:
            # Module has no tasks, ignore
            if "No module named" not in str(e):
                log.warn('[%s] No handlers loaded for [%s]', self.name, self.module)
                log.exception(e)

    def setup_handlers(self, adapter):
        """Override this to setup handlers directly from this plugin"""
        pass

    def setup_schedules(self, adapter):
        """Override this to setup schedules"""
        pass

    def load(self):
        log.info("Loading plugin [%s]", self.name)
        if not self.modspec:
            raise ValueError('Modspec is required')
        self.module = importlib.import_module(self.modspec)
        self._do_configure()
        self._do_load_models()
        self._do_setup_handlers()

    def add_handler(self, handler, priority=DEFAULT_PRIORITY):
        self.adapter.add_handler(handler, priority=priority, plugin=self)

    def provide_blueprint(self, config: dict) -> Blueprint:
        """Returns a flask blueprint, if the plugin provides one"""
        return None

    def __str__(self):
        return "{name}".format(name=self.modspec)

    def configure_oauth_from_config(self, config: dict):
        for client_config in config:
            name = client_config.pop('name', None)
            if not name:
                raise ValueError('Missing name for client config')
            key = OAuthClientKey(plugin_name=self.name, client_name=name)
            client = OAuthClientConfig(**client_config)
            client.client_key = key
            client.save()
            log.info('Registered OAuth client: %s', client)
