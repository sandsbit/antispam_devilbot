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

from typing import List, Tuple


from antispam.utils.singleton import SingletonMeta
from antispam.utils.db import DBUtils


class ChatsManager(metaclass=SingletonMeta):
    """Store list of all bot's chats in database"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    def get_all_chats(self) -> List[int]:
        """Returns list of IDs of all bot's chats"""
        self.blog.debug('Getting list of all chats')
        resp = self.db.run_single_query('select * from chats')
        result = [i[1] for i in resp]
        return result

    def add_new_chat(self, id_: int) -> None:
        """Add new bot's chat id"""
        self.blog.info(f'Adding new chat with id #{id_}')
        result = self.db.run_single_query('select * from chats where chat_id = %s', [id_])
        if len(result) == 0:
            self.db.run_single_update_query('insert into skarma.chats (chat_id) VALUES (%s)', [id_])
        else:
            self.blog.debug(f'Adding new chat with id #{id_} aborted: chat already exists')

    def remove_chat(self, chat_id: int) -> None:
        """Remove chat from database. Can be used even if this chat is already deleted"""
        self.blog.info(f'Removing from database chat with id #{chat_id}')
        self.db.run_single_update_query('delete from skarma.chats where chat_id = %s', [chat_id])


class AnnouncementsManager(metaclass=SingletonMeta):
    """Add or get announcements from database"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    def __init__(self):
        self.blog.info('Creating AnnouncementsManager instance')
        self.db.setup_new_connection(1)

    def get_all_announcements(self) -> List[Tuple[int, str]]:
        """Returns list of tuples, that store announcements' IDs and messages"""
        self.blog.debug(f'Getting list of all announcements')

        return self.db.run_single_query('select * from announcements', connection_id=1)

    def add_new_announcement(self, msg: str) -> None:
        """Add new announcement to database"""
        self.blog.debug(f'Adding new announcement')

        self.db.run_single_update_query('insert into skarma.announcements (text) VALUES (%s)', [msg], connection_id=1)

    def delete_announcement(self, id_: int) -> None:
        """Delete announcement from database by its id"""
        self.blog.debug(f'Removing announcement with id = {id_}')

        self.db.run_single_update_query('delete from announcements where id = %s', [id_], connection_id=1)
