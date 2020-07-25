#               _   _                                  _            _ _ _           _
#    __ _ _ __ | |_(_)___ _ __   __ _ _ __ ___      __| | _____   _(_) | |__   ___ | |_
#   / _` | '_ \| __| / __| '_ \ / _` | '_ ` _ \    / _` |/ _ \ \ / / | | '_ \ / _ \| __|
#  | (_| | | | | |_| \__ \ |_) | (_| | | | | | |  | (_| |  __/\ V /| | | |_) | (_) | |_
#   \__,_|_| |_|\__|_|___/ .__/ \__,_|_| |_| |_|___\__,_|\___| \_/ |_|_|_.__/ \___/ \__|
#                        |_|                  |_____|
#
# Remove excess mentions in telegram groups
# Copyright (C) 2020 Nikita Serba. All rights reserved
# https://github.com/sandsbit/antispam_devilbot
#
# antispam_devilbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# antispam_devilbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with antispam_devilbot. If not, see <https://www.gnu.org/licenses/>.

import logging

from typing import Optional, List, Tuple
from os import path

from telegram import Update
from telegram.ext import CallbackContext

from antispam.config_parsers.app_info import AppInfo
from antispam.utils.db import DBUtils
from antispam.utils.errorm import ErrorManager, catch_error
from antispam.announcements import ChatsManager
from antispam.banned_mentions import MentionBanManager, ViolationsManager
from antispam.usernames import UsernamesManager, NoSuchUser

LICENSE_FILE = "copyinfo.txt"

LICENSE_FILE = path.join(path.dirname(path.abspath(__file__)), '../config', LICENSE_FILE)

license_str: str

with open(LICENSE_FILE, encoding='utf-8') as f:
    license_str = f.read()


@catch_error
def version(update, context):
    """Send information about bot"""
    logging.getLogger('botlog').info('Printing version info to chat with id ' + str(update.effective_chat.id))

    bot_info = AppInfo()
    message = f"{bot_info.app_name} {bot_info.app_version}\n" \
              f"{bot_info.app_description}\n" \
              f"Build: {bot_info.app_build}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


@catch_error
def status(update, context):
    """Send information about bot status"""
    blog = logging.getLogger('botlog')
    blog.info('Printing status info to chat with id ' + str(update.effective_chat.id))

    number_of_errors = ErrorManager().get_number_of_errors()
    message = f"Status: Running in DEBUG mode ({'Stable' if number_of_errors == 0 else 'Unstable'})\n" \
              f"Unexpected errors: {number_of_errors} (/clear_errors)\n" \
              f"Logging status: " + ("logging normally\n" if len(blog.handlers) != 0 else "logging init failed\n") + \
              f"Database connection status: " + ("connected" if DBUtils().is_connected() else "disconnected (error)")
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


@catch_error
def support(update, context):  # TODO: read links from config file
    """Send information about bot status"""
    logging.getLogger('botlog').info('Printing support info to chat with id ' + str(update.effective_chat.id))

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Вы можете задать свой вопрос или преложить идею для бота по адрессу '
                                  'https://github.com/sandsbit/antispam_devilbot/issues (толькпо по англ.) или '
                                  'же по написв на почту <nikitaserba@icloud.com>.')


@catch_error
def bug_report(update, context):
    """Send information about bot status"""
    logging.getLogger('botlog').info('Printing bug report info to chat with id ' + str(update.effective_chat.id))

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Сообщить об ошибке можно по адрессу https://github.com/sandsbit/antispam_devilbot/issues '
                                  '(толькл по англ.). Используйте эту форму только для сообщения об технических '
                                  'ошибках. Если вас не устраивает что вам/кому-то подняли/опустили карму без повода, '
                                  'обратитесь к администратору группы. Если вы нашли узявимость в боте, ознакомтесь с '
                                  'https://github.com/sandsbit/antispam_devilbot/blob/master/SECURITY.md')


@catch_error
def gen_error(update, context):
    """Generate sample error for debugging"""

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logging.getLogger('botlog').info(f'Generating sample error! Asked by user #{user_id} in chat #{chat_id}')

    if user_id in AppInfo().admins:
        ErrorManager().report_error('Test error', f'This sample error was generated for debugging '
                                                  f'by user #{user_id} in chat #{chat_id}')
        context.bot.send_message(chat_id=chat_id, text='Sample error successfully generated')
    else:
        logging.getLogger('botlog').debug('Error could bot be generated: access denied. Check admins list')
        context.bot.send_message(chat_id=chat_id, text='Только администратор может сгенерировать тестовую ошибку')


@catch_error
def hhelp(update, context, custom_first_line: Optional[str] = None):
    chat_id = update.effective_chat.id
    logging.getLogger('botlog').info(f'Sending help to chat #{chat_id}')

    if custom_first_line is not None:
        help_ = custom_first_line + '\n\n'
    else:
        help_ = 'Нужна помощь? Ловите!\n\n'

    help_ += 'Ммммм тут еще ниче нет!'
    context.bot.send_message(chat_id=chat_id, text=help_)


@catch_error
def start(update, context):
    """Save user's chat id"""
    hhelp(update, context, 'Добро пожаловать!')

    chat_id = update.effective_chat.id
    logging.getLogger('botlog').info(f'User with id #{chat_id} will be added to database after running /start')
    ChatsManager().add_new_chat(chat_id)


@catch_error
def clear_errors(update, context):
    """Clear all errors in DB"""

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logging.getLogger('botlog').info(f'Deleting all errors! Asked by user #{user_id} in chat #{chat_id}')

    if user_id in AppInfo().admins:
        ErrorManager().clear_all_errors()
        context.bot.send_message(chat_id=chat_id, text='All errors successfully deleted')
    else:
        logging.getLogger('botlog').debug('Errors could bot be deleted: access denied. Check admins list')
        context.bot.send_message(chat_id=chat_id, text='Только администратор может удалить все ошибки')


@catch_error
def chat_id_(update, context):
    """Print chat id"""

    chat_id = update.effective_chat.id

    logging.getLogger('botlog').info(f'Printing chat id in chat #{chat_id}')
    context.bot.send_message(chat_id=chat_id, text=f'Current chat id: {chat_id}')


@catch_error
def dont_disturb_me(update, context):
    """Add user to dont disturb  list"""

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if hasattr(update.effective_user, 'username') and update.effective_user.username is not None:
        username = update.effective_user.username
    else:
        context.bot.send_message(chat_id=chat_id, text=f'У вас нет юзернейма :(, установите его в настройках '
                                                       f'и попробуйте еще раз.')
        return

    logging.getLogger('botlog').info(f'Add user #{user_id} in chat #{chat_id} to dont disturb list')

    new_value = MentionBanManager().set_user_ban_mention(chat_id, user_id)
    if new_value:
        context.bot.send_message(chat_id=chat_id, text=f'Упоминать {username} теперь могу только я!')
    else:
        context.bot.send_message(chat_id=chat_id, text=f'Упоминать {username} теперь могу только все!')


def process_list(bd_resp: List[int]) -> str:
    message = ''

    if len(bd_resp) == 0:
        message += f'В списке никого нет!'

    for user_id in bd_resp:
        try:
            message += UsernamesManager().get_username_by_id(user_id) + '\n'
        except NoSuchUser:
            message += f'Unnamed user ({user_id})\n'

    return message


def process_top(bd_resp: List[Tuple[int, int]]) -> str:
    message = ''

    if len(bd_resp) == 0:
        message += f'В ТОПе никого нет :)'

    for user_id, violations in bd_resp:
        try:
            user_name = UsernamesManager().get_username_by_id(user_id)
        except NoSuchUser:
            user_name = f'Unnamed user ({user_id})'
        message += f'{user_name}: {violations}\n'

    return message


@catch_error
def top(update, context):
    """Print top 5 of chat"""

    chat_id = update.effective_chat.id

    logging.getLogger('botlog').info(f'Printing TOP-5 user in chat #{chat_id}')

    message = 'ТОП-5 людей с наибольшим количеством нарушений:\n\n'

    top_ = ViolationsManager().get_ordered_violations_top(chat_id, 5)
    message += process_top(top_)

    context.bot.send_message(chat_id=chat_id, text=message)


@catch_error
def list_c(update: Update, context: CallbackContext):
    """Add user to dont disturb  list"""

    chat_id = update.effective_chat.id

    logging.getLogger('botlog').info(f'Printing list of users with banned mentions in chat #{chat_id}')

    message = 'Список людей, которых нельзя упоминать:\n\n'
    list_ = MentionBanManager().get_all_users_ban_mention(chat_id)
    message += process_list(list_)

    context.bot.send_message(chat_id=chat_id, text=message)


@catch_error
def stats(update: Update, context: CallbackContext):
    """Add user to dont disturb  list"""

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    logging.getLogger('botlog').info(f'Printing stats of user #{user_id} in chat #{chat_id}')

    violations_today, violations_month, violations_all = ViolationsManager().get_user_stats(chat_id, user_id)
    if violations_today == 0 and violations_month == 0 and violations_all == 0:
        message = 'Ммм да вы ещё ничего не натворили, чудо!'
    else:
        message = f'Увы, нарушения у вас есть:\n\n' \
                  f'Нарушений седня: {violations_today}\n' \
                  f'Нарушений в этом месяце: {violations_month}\n' \
                  f'Нарушений всего: {violations_all}\n'
    context.bot.send_message(chat_id=chat_id, text=message)


@catch_error
def license_(update, context):
    """Send information about bot status"""
    logging.getLogger('botlog').info('Printing license info to chat with id ' + str(update.effective_chat.id))

    ai = AppInfo()

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'{ai.app_name} {ai.app_version} (build: {ai.app_build})\n\n'
                                  f'{license_str}')
