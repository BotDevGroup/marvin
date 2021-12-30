from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized
from marvinbot.core import get_adapter, BANNED_IDS_CACHE_KEY
from marvinbot.cache import cache
from marvinbot.signals import bot_started, bot_shutdown, plugin_reload, joined_chat, left_chat
from marvinbot.handlers import CommandHandler, MessageHandler, CallbackQueryHandler
from marvinbot.defaults import DEFAULT_ROLE, OWNER_ROLE, POWER_USERS, RoleType
from marvinbot.models import User, make_token

import logging

log = logging.getLogger(__name__)
adapter = get_adapter()


@bot_started.connect
def on_start(adapter):
    adapter.notify_owners('✅ *Bot started*.', parse_mode='Markdown')


@bot_shutdown.connect
def on_shutdown(adapter):
    adapter.notify_owners('❌ *Bot shutting down*.', parse_mode='Markdown')


def format_plugins():
    result = []
    for plugin in adapter.plugin_registry.values():
        result.append('*{name}*: {enabled}'.format(
            name=plugin.name,
            enabled='✅' if plugin.enabled else '❌'
        ))
    if result:
        return "\n".join(result)
    return "❌ No plugins registered."


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

    update.effective_message.reply_text(format_plugins(), parse_mode='Markdown')


def authenticate(update, *args, **kwargs):
    token = kwargs.get('token')
    if update.effective_message.reply_to_message:
        target, created = User.from_telegram(update.effective_message.reply_to_message.from_user)
        if created:
            pass
        elif target.banned:
            update.effective_message.reply_text("User is *banned*.", parse_mode='Markdown')
        else:
            update.effective_message.reply_text("User role is: *{}*.".format(target.role), parse_mode='Markdown')
        return

    u, created = User.from_telegram(update.effective_message.from_user)

    owners = User.objects.filter(role=RoleType.OWNER)
    if u not in owners and not token and not created:
        update.effective_message.reply_text("Your role is: *{}*.".format(u.role), parse_mode='Markdown')
        return
    if u in owners:
        update.effective_message.reply_text("You are my master.")
        return

    if not created and make_token(u) == token:
        u.role = OWNER_ROLE
        u.auth_token = None
        u.save()

        update.effective_message.reply_text("Reporting for duty, master.", parse_mode='Markdown')
    elif not token:
        # New user, provide instructions to become the owner
        u.auth_token = make_token(u)
        u.save()
        log.info("Auth Token: {}".format(u.auth_token))
        update.effective_message.reply_text("Check the logs and provide the printed token to this command.",
                                  parse_mode='Markdown')


def manage_users(update, *args, **kwargs):
    role = kwargs.get('role', None)
    if role is not None:
        try:
            role = RoleType[role.upper()]
        except KeyError:
            update.effective_message.reply_text('❌ Invalid role specified.')
            return

    if not update.effective_message.reply_to_message:
        update.effective_message.reply_text('❌ Use this command while replying to a user.')
        return

    current_user, created = User.from_telegram(update.message.from_user)
    if role == OWNER_ROLE and current_user.role != OWNER_ROLE:
        update.effective_message.reply_text('❌ Only owners can add new owners.')

    u, created = User.from_telegram(update.effective_message.reply_to_message.from_user)
    if kwargs.get('forget', False):
        u.delete()
        update.effective_message.reply_text('🚮 Who _was_ that anyways?', parse_mode='Markdown')
        return

    if role:
        u.role = role
        update.effective_message.reply_text('✅ User permissions updated.')

    if kwargs.get('ignore', False):
        if u.role in POWER_USERS:
            update.effective_message.reply_text("❌ Can't ban an admin/owner.")
            return
        u.banned = True
        update.effective_message.reply_text('🔨 Applying BanHammer!', parse_mode='Markdown')
    elif kwargs.get('unignore', False):
        u.banned = False
        update.effective_message.reply_text('Not ignoring this user anymore.', parse_mode='Markdown')
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
        update.effective_message.reply_text('\n'.join(lst))
    else:
        update.effective_message.reply_text('❌ No commands registered.')


def membership_changed(update, *args, **kwargs):
    title = update.message.chat.title
    message = update.effective_message
    if message is None:
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.username:
        chat = '{title} (@{chat_username})'.format(title=title, chat_username=chat.username)
    else:
        chat = '{title} ({id})'.format(title=title, id=chat.id)

    first_name = user.first_name
    last_name = user.last_name
    username = user.username
    responsible = '{first_name} {last_name} (@{username})'.format(first_name=first_name,
                                                                  last_name=last_name,
                                                                  username=username)

    if len(message.new_chat_members) or\
            message.channel_chat_created or\
            message.group_chat_created or\
            message.supergroup_chat_created:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Leave', callback_data='bot:leave_chat:{}'.format(message.chat_id))]
        ])
        adapter.notify_owners('🚪 <b>Joined chat:</b> {chat}\nInvited by {responsible}'.format(chat=chat,
                                                                                              responsible=responsible),
                              parse_mode='HTML',
                              reply_markup=reply_markup)
        joined_chat.send(update)

    elif message.left_chat_member:
        adapter.notify_owners('🚪 <b>Left chat:</> {chat}\nKicked by {responsible}'.format(chat=chat,
                                                                                          responsible=responsible),
                              parse_mode='HTML')
        left_chat.send(update)

def on_leave_chat(update):
    query = update.callback_query
    message = query.message
    chat_id = query.data.split(':')[2]
    query.answer()
    message.edit_reply_markup(reply_markup=None)
    try:
        adapter.bot.leaveChat(chat_id)
    except Unauthorized as err:
        message.chat.send_message(text='❌ {}'.format(err.message))

def filter_bot_membership_change(message):
    return any(new_chat_member.id == adapter.bot_info.id for new_chat_member in message.new_chat_members) or\
        (message.left_chat_member and message.left_chat_member.id == adapter.bot_info.id) or\
        message.channel_chat_created or message.group_chat_created or message.supergroup_chat_created


def help_command(update):
    return commands_list(update, exclude_internal=True, plain=False)


adapter.add_handler(CommandHandler('plugins', plugin_control,
                                   command_description='[Admin] Enable/Disable plugins. If no arguments are passed, '
                                   'display a list of registered plugins.', required_roles=POWER_USERS)
                    .add_argument('--enable', nargs='+', metavar="PLUGIN", help='enables the listed plugins.')
                    .add_argument('--disable', nargs='+', metavar="PLUGIN", help='disables the listed plugins.')
                    .add_argument('--reload', nargs='+', metavar="PLUGIN", help='signals the specified plugins to reload, if supported.'), 0)

adapter.add_handler(CommandHandler('authenticate', authenticate, command_description='Authenticate yourself to the bot.')
                    .add_argument('token', nargs='?', help='your authentication token.'), 0)

adapter.add_handler(CommandHandler('users', manage_users, required_roles=POWER_USERS,
                                   command_description='Add a user', unauthorized_response='❌ You don\'t have permission to use this command.')
                    .add_argument('--role', choices=[role.name.lower() for role in RoleType])
                    .add_argument('--forget', action='store_true', help='Forget this user exists.')
                    .add_argument('--ignore', action='store_true', help='Ignore all updates from this user.')
                    .add_argument('--unignore', action='store_true', help='Stop ignoring all updates from this user.'), 0)

adapter.add_handler(CommandHandler('commands_list', commands_list,
                                   command_description='Returns a list of commands supported by the bot.')
                    .add_argument('--exclude_internal', action='store_true', help="Exclude internal bot commmands.")
                    .add_argument('--plain', action='store_true', help='Plain format (for sending to @BotFather).'), 0)

adapter.add_handler(CommandHandler('help', help_command, command_description='Provides help.'), 0)

adapter.add_handler(MessageHandler([filter_bot_membership_change], membership_changed, strict=True), 0)

adapter.add_handler(CallbackQueryHandler('bot:leave_chat', on_leave_chat), priority=1)
