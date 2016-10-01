from blinker import signal

bot_started = signal('bot_started')
bot_shutdown = signal('bot_shutdown')

# Sent when the bot is added to a channel
new_channel = signal('new_channel')
