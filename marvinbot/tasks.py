from marvinbot.celeryapp import marvinbot_app
from marvinbot.core import get_adapter
from celery.utils.log import get_task_logger
from marvinbot.signals import bot_started, bot_shutdown
from marvinbot.models import User
from marvinbot.handlers import CommandHandler, Filters


log = get_task_logger(__name__)
adapter = get_adapter()


@bot_started.connect
def on_start(adapter):
    adapter.notify_owners('✅ *Bot started*')


@bot_shutdown.connect
def on_shutdown(adapter):
    adapter.notify_owners('❌ *Bot shutting down*')


@marvinbot_app.task
def you_there(update, *args, **kwargs):
    update.message.reply_text('Me here 👀, are _you_?', parse_mode='Markdown')


adapter.add_handler(CommandHandler('test', you_there, call_async=False))
