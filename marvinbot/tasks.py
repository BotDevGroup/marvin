from marvinbot.core import get_adapter, BANNED_IDS_CACHE_KEY
from marvinbot.cache import cache
from marvinbot.signals import bot_started, bot_shutdown, plugin_reload, new_channel, left_channel
from marvinbot.handlers import CommandHandler, MessageHandler
from marvinbot.defaults import USER_ROLES, DEFAULT_ROLE, OWNER_ROLE, POWER_USERS
from marvinbot.models import User, make_token
import logging

log = logging.getLogger(__name__)
adapter = get_adapter()


@bot_started.connect
def on_start(adapter):
    adapter.notify_owners('✅ *Bot started*')


@bot_shutdown.connect
def on_shutdown(adapter):
    adapter.notify_owners('❌ *Bot shutting down*')


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
            p = adapter.plugin_definition(plugin)
            if p.enabled:
                plugin_reload.send(p, update=update)

    update.message.reply_text(format_plugins(), parse_mode='Markdown')


def authenticate(update, *args, **kwargs):
    token = kwargs.get('token')
    if update.message.reply_to_message:
        target, created = User.from_telegram(update.message.reply_to_message.from_user)
        if created:
            pass
        elif target.banned:
            update.message.reply_text("User is *banned*", parse_mode='Markdown')
        else:
            update.message.reply_text("User role is: *{}*".format(target.role), parse_mode='Markdown')
        return

    u, created = User.from_telegram(update.message.from_user)

    owners = User.objects.filter(role='owner')
    if u not in owners and not token and not created:
        update.message.reply_text("Your role is: *{}*".format(u.role), parse_mode='Markdown')
        return
    if u in owners:
        update.message.reply_text("You are my master")
        return

    if not created and make_token(u) == token:
        u.role = OWNER_ROLE
        u.auth_token = None
        u.save()

        update.message.reply_text("Reporting for duty, master.", parse_mode='Markdown')
    elif not token:
        # New user, provide instructions to become the owner
        u.auth_token = make_token(u)
        u.save()
        log.info("Auth Token: {}".format(u.auth_token))
        update.message.reply_text("Check the logs and provide the printed token to this command.",
                                  parse_mode='Markdown')


def manage_users(update, *args, **kwargs):
    role = kwargs.get('role')
    if not update.message.reply_to_message:
        update.message.reply_text('❌ Use this command while replying to a user')

    current_user, created = User.from_telegram(update.message.from_user)
    if role == OWNER_ROLE and current_user.role != OWNER_ROLE:
        update.message.reply_text('❌ Only owners can add new owners')

    u, created = User.from_telegram(update.message.reply_to_message.from_user)
    if kwargs.get('forget', False):
        u.delete()
        update.message.reply_text('🚮 Who _was_ that anyways?', parse_mode='Markdown')
        return

    if role:
        u.role = role
        update.message.reply_text('✅ User permissions updated')

    if kwargs.get('ignore', False):
        if u.role in POWER_USERS:
            update.message.reply_text("❌ Can't ban an admin/owner")
            return
        u.banned = True
        update.message.reply_text('🔨 Applying BanHammer!', parse_mode='Markdown')
    elif kwargs.get('unignore', False):
        u.banned = False
        update.message.reply_text('Not ignoring this user anymore.', parse_mode='Markdown')
    cache.delete(BANNED_IDS_CACHE_KEY)
    u.save()


def commands_list(update, *args, **kwargs):
    exclude_internal = kwargs.get('exclude_internal')
    plain = kwargs.get('plain')
    bot_name = adapter.bot_info.username
    lst = []
    for cmd in adapter.commands(exclude_internal).values():
        lst.append('{prefix}{cmd}{bot_name} - {description}'.format(cmd=cmd.command,
                                                                    description=cmd.description,
                                                                    prefix='' if plain else '/',
                                                                    bot_name='' if plain else '@' + bot_name))

    if lst:
        update.message.reply_text('\n'.join(lst))
    else:
        update.message.reply_text('No commands registered')


def channel_changed(update, *args, **kwargs):
    channel = '{title}'.format(title=update.message.chat.title)
    responsible = '{first_name} {last_name} ({username})'.format(first_name=update.message.from_user.first_name,
                                                                 last_name=update.message.from_user.last_name,
                                                                 username=update.message.from_user.username)

    if update.message.new_chat_member:
        adapter.notify_owners('*New channel:* _{channel_name}_, added by _{responsible}_'.format(channel_name=channel,
                                                                                                 responsible=responsible))
        new_channel.send(update)
    elif update.message.left_chat_member:
        adapter.notify_owners('*Left channel:* _{channel_name}_, added by _{responsible}_'.format(channel_name=channel,
                                                                                                  responsible=responsible))
        left_channel.send(update)


def filter_bot_channel_change(message):
    return (bool(message.new_chat_member) or bool(message.left_chat_member)) and\
        (message.new_chat_member.id == adapter.bot_info.id or message.left_chat_member.id == adapter.bot_info.id)


adapter.add_handler(CommandHandler('plugins', plugin_control,
                                   command_description='[Admin] Enable/Disable plugins. If no arguments are passed, '
                                   'display a list of registered plugins', required_roles=POWER_USERS)
                    .add_argument('--enable', nargs='+', metavar="PLUGIN", help='enables the listed plugins')
                    .add_argument('--disable', nargs='+', metavar="PLUGIN", help='disables the listed plugins')
                    .add_argument('--reload', nargs='+', metavar="PLUGIN", help='signals the specified plugins to reload, if supported'), 0)

adapter.add_handler(CommandHandler('authenticate', authenticate, command_description='Authenticate yourself to the bot')
                    .add_argument('token', nargs='?', help='your authentication token'), 0)

adapter.add_handler(CommandHandler('users', manage_users, required_roles=POWER_USERS,
                                   command_description='Add a user', unauthorized_response='403, motherfucker')
                    .add_argument('--role', choices=USER_ROLES)
                    .add_argument('--forget', action='store_true', help='Forget this user exists')
                    .add_argument('--ignore', action='store_true', help='Ignore all updates from this user')
                    .add_argument('--unignore', action='store_true', help='Stop ignoring all updates from this user'), 0)

adapter.add_handler(CommandHandler('commands_list', commands_list,
                                   command_description='Returns a list of commands supported by the bot')
                    .add_argument('--exclude_internal', action='store_true', help="Exclude internal bot commmands")
                    .add_argument('--plain', action='store_true', help='Plain format (for sending to @BotFather)'), 0)

adapter.add_handler(MessageHandler([filter_bot_channel_change], channel_changed, strict=True), 0)
