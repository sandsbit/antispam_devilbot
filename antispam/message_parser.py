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

import time
import logging

from threading import Thread
from telegram import Bot, ChatPermissions
from telegram.error import TimedOut, RetryAfter, Unauthorized

from antispam.utils.errorm import ErrorManager, catch_error
from antispam.utils.db import DBUtils
from antispam.announcements import ChatsManager, AnnouncementsManager
from antispam.commands import hhelp
from antispam.usernames import UsernamesManager, NoSuchUser
from antispam.banned_mentions import MentionBanManager, ViolationsManager, Sanction


class AnnouncementsThread(Thread):
    """This thread checks for announcements and send them if there are any"""

    blog = logging.getLogger('botlog')

    chats = []
    last_chats_change_time = -1

    bot: Bot

    def __init__(self, bot: Bot):
        Thread.__init__(self)

        self.blog.info('Creating new announcements thread instance')

        self.change_chats_if_needed()
        self.bot = bot

    def change_chats_if_needed(self) -> bool:
        """
        Reloads chats list from database if it hasn't been reloaded for five minutes

        Returns true if chats was reloaded and false if it five minutes hasn't passed since last reload.
        """
        self.blog.info('Checking if its needed to update chats list')
        current_time = time.time()
        time_change = current_time - self.last_chats_change_time
        if time_change > 5*60:
            self.blog.debug(f"It's been {time_change/60} minutes since last chats list update. Updating...")
            self.chats = ChatsManager().get_all_chats()
            return True
        self.blog.debug("There is no need in updating chats list")
        return False

    def _try_send_message(self, chat_id: int, msg: str):
        i = 0
        while True:
            i += 1

            if i == 10:
                raise TimeoutError('Message sending failed after 10 attempts')

            succ = False
            try:
                self.bot.send_message(chat_id=chat_id, text=msg)
                succ = True
            except TimedOut:
                self.blog.warning('Timout while sending message (we will try one more time): ', exc_info=True)
            except RetryAfter as e:
                self.blog.warning('Telegram send retry_after while sending message (we will try one more time): ',
                                  exc_info=True)
                time.sleep(e.retry_after)
            except Unauthorized:
                self.blog.info(f'Bot was blocked by user with id #{chat_id}')
                ChatsManager().remove_chat(chat_id)
                succ = True
            except Exception as e:
                self.blog.error(e)
                ErrorManager().report_exception(e)
                succ = True

            if succ:
                break

    def run(self) -> None:
        am = AnnouncementsManager()
        while True:
            self.change_chats_if_needed()

            announcements = am.get_all_announcements()

            for id_, msg in announcements:
                self.blog.info(f'Sending new announcement with id ${id_}')
                for chat_id in self.chats:
                    self.blog.debug(f'Sending new announcement with id ${id_} into chat with id #{chat_id}')
                    self._try_send_message(chat_id, msg)
                    time.sleep(2)
                am.delete_announcement(id_)
            time.sleep(10*60)


@catch_error
def handle_mention_violation(update, context):
    """Check message for banned mentions"""

    blog = logging.getLogger('botlog')
    bmm, vm = MentionBanManager(), ViolationsManager()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    text = update.message.text

    mentions = []

    if update.effective_user.is_bot:
        return

    for entity in update.message.entities:
        if entity.type == 'mention':
            b, len_ = entity.offset, entity.length

            mentions.append(text[b, b+len_])

    if len(mentions) == 0:
        return

    banned_mentions = bmm.get_all_users_ban_mention(chat_id)
    banned_mentions_dict = dict()
    for bm in banned_mentions:
        try:
            banned_mentions_dict[UsernamesManager().get_username_by_id(bm)] = bm
        except NoSuchUser:
            pass

    violations_id = []
    for mention in mentions:
        if mention in banned_mentions_dict.keys() and mention != username:
            violations_id.append(banned_mentions_dict[mention])

    if len(violations_id) != 0:
        sanctions = vm.register_violation(chat_id, user_id, violations_id)

        mention_list = ', '.join([UsernamesManager().get_username_by_id(id_)[1:] for id_ in violations_id])
        message = f'Упс! {username} упомянул {mention_list}, что есть не по правилам :(. '

        if len(sanctions) > 2:
            raise RuntimeError('Invalid sanctions list')

        if sanctions[0] == Sanction.WARNING:
            message += 'Больше так не делай! Это первое и последнее предупреждение!'
        elif sanctions[0] == Sanction.MUTE_FIVE_MIN:
            message += 'За это {username} получит мут на пять минут!'

            context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(False),
                                             until_date=int(time.time()) + 300)
        elif sanctions[0] == Sanction.MUTE_HOUR:
            message += 'За это {username} получит мут на час!'

            context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(False),
                                             until_date=int(time.time()) + 3600)
        elif sanctions[0] == Sanction.MUTE_DAY:
            message += 'За это {username} получит мут на день!'

            context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(False),
                                             until_date=int(time.time()) + 3600*24)

        if len(sanctions) == 2:
            media_ban_permissions = ChatPermissions(True, False, False, False, False, False, False, False)
            if sanctions[1] == Sanction.BAN_MEDIA_WEEK:
                message += ' Запрет отправки медиа на неделю так же не будет лишним :/'

                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=media_ban_permissions,
                                                 until_date=int(time.time()) + 3600*24*7)
            if sanctions[1] == Sanction.BAN_MEDIA_MONTH:
                message += ' Запрет отправки медиа на месяц так же не будет лишним :/'

                context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=media_ban_permissions,
                                                 until_date=int(time.time()) + 3600*24*31)

        context.bot.send_message(chat_id=chat_id, text=message)


@catch_error
def handle_group_migration_or_join(update, context):
    UsernamesManager().set_username(update.effective_user.id, update.effective_user.username)

    if update.message is not None:
        if update.message.new_chat_members is not None:
            for new_member in update.message.new_chat_members:
                if new_member.id == context.bot.id:
                    chat_id = update.effective_chat.id
                    logging.getLogger('botlog').info(f'Group with id #{chat_id} will be added to database after adding bot to it')
                    hhelp(update, context, 'Добро пожаловать!')
                    ChatsManager().add_new_chat(chat_id)
        if update.message.migrate_to_chat_id is not None:
            old_chat_id = update.effective_chat.id
            new_chat_id = update.message.migrate_to_chat_id

            logging.getLogger('botlog').info(f'Migrating chat from #{old_chat_id} to #{new_chat_id}')

            db = DBUtils()

            tables = ['chats', 'karma', 'stats']
            for table in tables:
                db.run_single_update_query(f'update {table} set chat_id = %s where chat_id = %s', (new_chat_id, old_chat_id))
