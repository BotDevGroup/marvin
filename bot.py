from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.config import config
from app.views import WarningView, ErrorView, InfoView

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s [%(name)s %(levelname)s]: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')],

                [InlineKeyboardButton("Option 3", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def echo(bot, update):
    update.message.reply_text(update.message.text)


def ping(bot, update):
    update.message.reply_text("pong")


def button(bot, update):
    query = update.callback_query

    bot.editMessageText(text="Selected option: %s" % query.data,
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id)


def info(bot, update):
    msg = InfoView("this is a test")
    # print(str(update).encode('utf8'))
    # update.message.reply_text("info")
    update.message.reply_text(str(msg))


def errorm(bot, update):
    msg = ErrorView("this is a test")
    update.message.reply_text(str(msg))


def warning(bot, update):
    msg = WarningView("this is a test")
    update.message.reply_text(str(msg))


def help(bot, update):
    update.message.reply_text(
        "Use /start to test this bot. Other commands: /echo, /ping")


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

# Create the Updater and pass it your bot's token.
updater = Updater(config.config["Debug"]["TelegramBotToken"])

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(button))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('echo', echo))
updater.dispatcher.add_handler(CommandHandler('ping', ping))
updater.dispatcher.add_handler(CommandHandler('info', info))
updater.dispatcher.add_handler(CommandHandler('warning', warning))
updater.dispatcher.add_handler(CommandHandler('error', errorm))
updater.dispatcher.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
