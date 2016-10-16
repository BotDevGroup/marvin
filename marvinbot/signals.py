from blinker import signal

bot_started = signal('bot_started')
bot_shutdown = signal('bot_shutdown')

# Sent when the bot is added to a channel
new_channel = signal('new_channel')

# Sent when a plugin finishes loading, receives the plugin as parameter
plugin_loaded = signal('plugin_loaded')

# Sent when an admin sends /reload plugin_name
plugin_reload = signal('plugin_reload')
