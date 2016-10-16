from marvinbot.core import get_adapter
from marvinbot.signals import bot_started, bot_shutdown, plugin_reload
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


def format_plugins():
    result = []
    for plugin in adapter.plugin_registry.values():
        result.append('*{name}*: {enabled}'.format(
            name=plugin.name,
            enabled='✅' if plugin.enabled else '❌'
        ))
    if result:
        return "\n".join(result)
    return "No plugins registered"


def plugin_control(update, *args, **kwargs):
    if kwargs.get('disable'):
        for plugin in kwargs.get('disable'):
            adapter.enable_plugin(plugin, False)

    if kwargs.get('enable'):
        for plugin in kwargs.get('enable', []):
            adapter.enable_plugin(plugin)

    if kwargs.get('reload'):
        for plugin in kwargs.get('reload', []):
            plugin_reload.send(adapter.plugin_definition(plugin), update=update)

    update.message.reply_text(format_plugins(), parse_mode='Markdown')


adapter.add_handler(CommandHandler('test', you_there,
                                   command_description="Sends back a simple response")
                    .add_argument('--foo', help='foo help')
                    .add_argument('--bar', help='bar help'), 0)

adapter.add_handler(CommandHandler('plugins', plugin_control,
                                   command_description='[Admin] Enable/Disable plugins. If no arguments are passed, '
                                   'display a list of registered plugins', required_roles=['admin', 'owner'])
                    .add_argument('--enable', nargs='+', metavar="PLUGIN", help='enables the listed plugins')
                    .add_argument('--disable', nargs='+', metavar="PLUGIN", help='disables the listed plugins')
                    .add_argument('--reload', nargs='+', metavar="PLUGIN", help='signals the specified plugins to reload, if supported'), 0)
