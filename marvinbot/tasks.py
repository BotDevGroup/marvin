from marvinbot.celeryapp import marvinbot_app
from marvinbot.core import get_adapter
from marvinbot.handlers import Filters, CommandHandler, MessageHandler
from celery.utils.log import get_task_logger


log = get_task_logger(__name__)
adapter = get_adapter()


@marvinbot_app.task()
def start_command(update, *args):
    log.info('Start command caught')
    adapter.bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!: {}".format(args))


@marvinbot_app.task()
def bowdown(update, *args):
    update.message.reply_text('Yes, master **bows**')


@marvinbot_app.task()
def gaze_at_pic(update):
    update.message.reply_text('Nice pic, bro')


@marvinbot_app.task()
def salutation_initiative(update):
    update.message.reply_text("'zup")


adapter.add_handler(CommandHandler('start', start_command, call_async=True))
adapter.add_handler(MessageHandler(Filters.photo, gaze_at_pic))
adapter.add_handler(MessageHandler([Filters.text, lambda msg: msg.text.lower() in ['hola', 'hi', 'klk', 'hey']],
                                   salutation_initiative,
                                   strict=True))
