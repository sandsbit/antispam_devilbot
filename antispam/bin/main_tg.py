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

import argparse
import logging
import logging.handlers
import os
import sys

from os import path

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from antispam import commands, message_parser, donate
from antispam.config_parsers.app_info import AppInfo
from antispam.utils.errorm import ErrorManager

LOGGING_DIR: str

if os.name == 'nt':
    LOGGING_DIR = r'%AppData%\antispam_devilbot\logs'  # only %AppData% can be used in path, other envs won't work
else:
    LOGGING_DIR = '/var/log/antispam_devilbot'


def setup_logging_ui() -> None:
    """
    UNIX:
    Setup logging into /var/log. If app don't have permission
    to access /var/log/antispam_devilbot, than error message will be printed.

    WINDOWS:
    Same as UNIX, but logging into %AppData%\santispam_devilbot\logs.
    """

    global LOGGING_DIR

    if os.name == 'nt':
        LOGGING_DIR = LOGGING_DIR.replace('%AppData%', os.getenv('APPDATA'))

        if not path.exists(LOGGING_DIR):
            os.makedirs(LOGGING_DIR)

    if not path.exists(LOGGING_DIR) or not path.isdir(LOGGING_DIR) or not os.access(LOGGING_DIR, os.W_OK):
        ErrorManager().report_error("Logging problem", "Can't access logging directory. Logging will be turned off.")
        print(f'Can\'t access logging directory.\n'
              f'Please, run "sudo mkdir -p {LOGGING_DIR} && sudo chown $(whoami) {LOGGING_DIR}"\n'
              f'Logging will be turned off.')
        return

    formatter = logging.Formatter('%(asctime)s - %(process)d - %(threadName)s (%(thread)d) '
                                  '- %(levelname)s - %(module)s - %(message)s')

    tglogger = logging.getLogger("telegram.bot")
    tglogger.setLevel(logging.DEBUG)

    tglogger.handlers = []

    botlogger = logging.getLogger('botlog')
    botlogger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    ifh = logging.handlers.TimedRotatingFileHandler(
        filename=path.join(LOGGING_DIR, 'bot-info.log'),
        when='d',
        backupCount=3
    )
    ifh.setLevel(logging.INFO)
    ifh.setFormatter(formatter)

    wfh = logging.handlers.TimedRotatingFileHandler(
        filename=path.join(LOGGING_DIR, 'bot-warn-error.log'),
        when='d',
        backupCount=7
    )
    wfh.setLevel(logging.WARN)
    wfh.setFormatter(formatter)

    tglogger.addHandler(sh)
    tglogger.addHandler(ifh)
    tglogger.addHandler(wfh)

    shm = logging.StreamHandler()
    shm.setLevel(logging.DEBUG)
    shm.setFormatter(formatter)

    ifhm = logging.handlers.TimedRotatingFileHandler(
        filename=path.join(LOGGING_DIR, 'debug.log'),
        when='d',
        backupCount=3
    )
    ifhm.setLevel(logging.DEBUG)
    ifhm.setFormatter(formatter)

    wfhm = logging.handlers.TimedRotatingFileHandler(
        filename=path.join(LOGGING_DIR, 'warn-error.log'),
        when='d',
        backupCount=7
    )
    wfhm.setLevel(logging.WARN)
    wfhm.setFormatter(formatter)

    botlogger.addHandler(shm)
    botlogger.addHandler(ifhm)
    botlogger.addHandler(wfhm)


if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print('Invalid python version. Use python 3.7 or newer')

    setup_logging_ui()

    blog = logging.getLogger('botlog')
    blog.info('Finished logging setup')
    blog.info('Starting bot')

    bot_info = AppInfo()

    blog.debug('Parsing arguments')
    parser = argparse.ArgumentParser(description=bot_info.app_description)

    parser.add_argument('--debug', '-d', help='Run bot dev version', action='store_true')

    result = parser.parse_args()
    DEBUG_MODE = result.debug

    if DEBUG_MODE:
        blog.info('Running in DEBUG mode')
        token = bot_info.app_dev_token
    else:
        blog.info('Running in INFO mode')
        token = bot_info.app_token

    blog.debug('Running with token: ' + token)

    if DEBUG_MODE:
        ErrorManager().report_by_email = False

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    blog.info('Created updater and dispatcher')

    dispatcher.add_handler(CommandHandler('version', commands.version))
    blog.info('Added handler for /version command')

    if DEBUG_MODE:
        dispatcher.add_handler(CommandHandler('status', commands.status))
        blog.info('Added handler for /status command')

    dispatcher.add_handler(CommandHandler('bug_report', commands.bug_report))
    blog.info('Added handler for /bug_report command')

    dispatcher.add_handler(CommandHandler('support', commands.support))
    blog.info('Added handler for /support command')

    dispatcher.add_handler(CommandHandler('start', commands.start))
    blog.info('Added handler for /start command')

    if DEBUG_MODE:
        dispatcher.add_handler(CommandHandler('gen_error', commands.gen_error))
        blog.info('Added handler for /gen_error command')

    dispatcher.add_handler(CommandHandler('help', commands.hhelp))
    blog.info('Added handler for /help command')

    dispatcher.add_handler(CommandHandler('license', commands.license_))
    blog.info('Added handler for /license command')

    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('donate', donate.donate_ask if not DEBUG_MODE else donate.donate_ask_d)],
        states={
            donate.AMOUNT: [MessageHandler(Filters.text & (~Filters.command),
                                           donate.donate if not DEBUG_MODE else donate.donate_d)]
        },

        fallbacks=[CommandHandler('cancel', donate.cancel)]
    ))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, donate.finish_donate))

    if DEBUG_MODE:
        dispatcher.add_handler(CommandHandler('clear_errors', commands.clear_errors))
        blog.info('Added handler for /clear_errors command')

    if DEBUG_MODE:
        dispatcher.add_handler(CommandHandler('chat_id', commands.chat_id_))
        blog.info('Added handler for /chat_id command')

    dispatcher.add_handler(MessageHandler(Filters.all, message_parser.handle_group_migration_or_join), group=2)
    blog.info('Added handler for group migration to supergroup or group join')

    dispatcher.add_handler(MessageHandler(Filters.all, message_parser.handle_mention_violation))
    blog.info('Added handler that checks mention violations')

    blog.info('Starting announcements thread')
    ann_thread = message_parser.AnnouncementsThread(updater.bot)
    ann_thread.start()

    blog.info('Starting polling')
    updater.start_polling()

    updater.idle()
