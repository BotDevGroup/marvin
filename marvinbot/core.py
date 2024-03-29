import abc
import time
import logging
from functools import partial
from collections import defaultdict, OrderedDict

from marvinbot.errors import HandlerException
from marvinbot.defaults import DEFAULT_PRIORITY
from marvinbot.models import User
from marvinbot.cache import cache
from marvinbot.plugins import Plugin
import telegram
from ratelimiter import RateLimiter


log = logging.getLogger(__name__)
PERIODIC_TASKS = OrderedDict()


_ADAPTER = None
ADAPTER_REGISTRY = {}
BANNED_IDS_CACHE_KEY = "marvinbot-banned-user-ids"


def configure_adapter(config):
    global _ADAPTER
    adapter_name = config.get("adapter_name", "telegram")
    adapter = ADAPTER_REGISTRY.get(adapter_name)
    _ADAPTER = adapter(config)
    return _ADAPTER


def get_adapter():
    global _ADAPTER
    if _ADAPTER:
        return _ADAPTER


def is_user_banned(user):
    user_id = user.id

    def get_banned_user_ids():
        return list(User.objects.filter(banned=True).scalar("id"))

    banned_ids = cache.get_or_create(
        BANNED_IDS_CACHE_KEY,
        get_banned_user_ids,
        should_cache_fn=lambda value: value is not None,
    )
    return user_id in banned_ids


class AdapterMeta(abc.ABCMeta):
    def __new__(mcs, name, bases, new_attrs):
        return super(AdapterMeta, mcs).__new__(mcs, name, bases, new_attrs)

    def __init__(cls, name, bases, attrs):
        cls._adapter_name = name.replace("Adapter", "").lower()
        ADAPTER_REGISTRY[cls.adapter_name] = cls
        super(AdapterMeta, cls).__init__(name, bases, attrs)

    @property
    def adapter_name(cls):
        return cls._adapter_name


class Adapter(object, metaclass=AdapterMeta):
    def __init__(self, config):
        self.config = config
        self.handlers = defaultdict(list)
        self.plugin_registry = {}

    def add_handler(self, handler, priority=DEFAULT_PRIORITY, plugin=None):
        if not plugin:
            plugin = self.plugin_for_handler(handler)
        handler.plugin = plugin

        log.info(
            "Adding handler: {}, priority: {}, plugin: {}".format(
                handler, priority, plugin
            )
        )
        self.handlers[priority].append(handler)

    def plugin_for_handler(self, handler):
        mod = handler.callback.__module__.split(".", 1)[0]
        plugins = self.plugins_by_modspec()
        if mod in plugins:
            return plugins[mod]

    def plugins_by_modspec(self):
        return {p.modspec: p for p in self.plugin_registry.values()}

    def add_plugin(self, plugin):
        if not isinstance(plugin, Plugin):
            raise ValueError("plugin must be a Plugin sublass")
        self.plugin_registry[plugin.name] = plugin

    def enable_plugin(self, plugin_name, enable=True):
        if plugin_name in self.plugin_registry:
            self.plugin_registry[plugin_name].enabled = enable

    def plugin_definition(self, plugin_name):
        return self.plugin_registry.get(plugin_name)

    def commands(self, exclude_internal=False):
        from marvinbot.handlers import CommandHandler

        result = OrderedDict()
        for priority, handlers in self.handlers.items():
            if exclude_internal and priority == 0:
                continue
            for handler in handlers:
                if exclude_internal and handler.plugin is None:
                    continue
                if isinstance(handler, CommandHandler):
                    result[handler.command] = handler
        return result

    @property
    def scheduler_available(self):
        return hasattr(self, "scheduler") and self.scheduler

    def add_job(self, func, *args, **kwargs):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")

        # Add the adapter for easy reference
        func.adapter = self
        return self.scheduler.add_job(func, *args, **kwargs)

    def pause_job(self, job_id):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")
        return self.scheduler.pause_job(job_id)

    def resume_job(self, job_id):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")
        return self.scheduler.resume_job(job_id)

    def remove_job(self, job_id):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")
        return self.scheduler.remove_job(job_id)

    def get_jobs(self):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")
        return self.scheduler.get_jobs()

    def get_job(self, job_id):
        if not self.scheduler_available:
            raise ValueError("Scheduler not available")
        return self.scheduler.get_job(job_id)

    @abc.abstractmethod
    def fetch_updates(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def process_update(self, update):
        raise NotImplementedError

    @abc.abstractmethod
    def notify_owners(self, message, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def make_updater(self):
        raise NotImplementedError

    @property
    def updater(self):
        if not self._updater:
            self._updater = self.make_updater()
        return self._updater


def on_rate_limited(until, key=None):
    duration = int(round(until - time.time()))
    log.info(f"Rate limiter hit for key {key}, sleeping for {duration} seconds")


RATE_LIMITERS = {
    "default": RateLimiter(
        max_calls=30, period=1, callback=partial(on_rate_limited, key="normal")
    )
}


class RateLimitedBot(telegram.Bot):
    @cache.cache_on_arguments(expiration_time=86400)
    def is_group_chat(self, chat_id):
        log.info("Getting info for chat_id [%s]", chat_id)
        chat_info = self.getChat(chat_id)
        chat_type = chat_info.type
        return chat_type in ["group", "supergroup"]

    def get_group_rate_limiter(self, chat_id):
        key = f"group-{chat_id}"
        if key not in RATE_LIMITERS:
            log.info("Making rate limiter for key [%s]", key)
            limiter = RateLimiter(
                max_calls=20, period=60, callback=partial(on_rate_limited, key=key)
            )
            RATE_LIMITERS[key] = limiter
        return RATE_LIMITERS[key]

    def send_message(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id") or args[0]
        if chat_id and self.is_group_chat(chat_id):
            rate_limiter = self.get_group_rate_limiter(chat_id)
            log.info("Using group rate limiter for group [%s]", chat_id)
        else:
            rate_limiter = RATE_LIMITERS["default"]
        with rate_limiter:
            return super(RateLimitedBot, self).send_message(*args, **kwargs)


class TelegramAdapter(Adapter):
    def __init__(self, config):
        token = config.get("telegram_token")
        self.bot = RateLimitedBot(token)
        self.bot_info = self.bot.getMe()
        self._updater = None
        super(TelegramAdapter, self).__init__(config)

    def fetch_updates(self, last_update_id=None):
        for update in self.bot.getUpdates(
            offset=last_update_id, timeout=int(self.config.get("fetch_timeout", 5))
        ):
            yield update

    def process_update(self, update):
        if update.effective_user and is_user_banned(update.effective_user):
            return
        log.debug("Processing message: %s", str(update.effective_message).encode("utf-8"))
        for priority in sorted(self.handlers):
            for handler in self.handlers[priority]:
                try:
                    log.debug("Trying handler: %s", str(handler))
                    if handler.plugin and not handler.plugin.enabled:
                        continue
                    if handler.can_handle(update):
                        log.debug("Using handler: %s", str(handler))
                        handler.process_update(update)
                        if not handler.is_final:
                            continue
                except Exception as e:
                    log.exception(e)
                    # self.notify_owners(r"⚠ Handler Error: ```{}```".format(traceback.format_exc()))
                    raise HandlerException from e

    def notify_owners(self, message: str, **kwargs):
        owners = User.objects.filter(role="owner")
        for owner in owners:
            self.bot.sendMessage(owner.id, message, **kwargs)

    def make_updater(self):
        from marvinbot.polling import TelegramPollingThread

        updater = TelegramPollingThread(self)
        return updater
