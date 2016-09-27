from marvinbot.celeryapp import marvinbot_app, adapter_generator as make_adapter
from marvinbot.cache import cache
from celery.utils.log import get_task_logger
from telegram.error import NetworkError, Unauthorized


log = get_task_logger(__name__)
adapter = make_adapter()


@marvinbot_app.task(bind=True)
def fetch_messages(self):
    try:
        for update in adapter.fetch_updates(cache.get('last_update_id', 30)):
            adapter.process_update(update)
            cache.set('last_update_id', update.update_id + 1)
    except NetworkError:
        log.info("No more updates to fetch")
    except Unauthorized:
        # The user has removed or blocked the bot.
        log.error("Unauthorized: User might have blocked a bot")


@adapter.register_command('start')
@marvinbot_app.task()
def start_command(update):
    log.info('Start command caught')
    adapter.bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")
