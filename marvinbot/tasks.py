from marvinbot.core import get_adapter
from marvinbot.signals import bot_started, bot_shutdown
from marvinbot.handlers import CommandHandler
import logging

log = logging.getLogger(__name__)
adapter = get_adapter()


@bot_started.connect
def on_start(adapter):
    adapter.notify_owners('✅ *Bot started*')


@bot_shutdown.connect
def on_shutdown(adapter):
    adapter.notify_owners('❌ *Bot shutting down*')


def you_there(update, *args, **kwargs):
    log.info("Responding to you_there: args: %s, kwargs: %s", str(args), str(kwargs))
    update.message.reply_text('Me here 👀, are _you_? args:"{}", kwargs: "{}"'.format(str(args), str(kwargs)),
                              parse_mode='Markdown')


adapter.add_handler(CommandHandler('test', you_there,
                                   command_description="Sends back a simple response")
                    .add_argument('--foo', help='foo help')
                    .add_argument('--bar', help='bar help'), 0)
