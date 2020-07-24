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

from typing import Optional, List
from enum import Enum

from antispam.utils.singleton import SingletonMeta
from antispam.utils.db import DBUtils


class MentionBanManager(metaclass=SingletonMeta):
    """Manage users that ban their mentions"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    def set_user_ban_mention(self, chat_id: int, user_id: int, ban_mentions: Optional[bool] = None) -> None:
        """Sets ban_mention for user. By default reverses value"""

        self.blog.info(f'Changing ban_mentions for user #{user_id} i chat #{chat_id} to {ban_mentions} (if None than'
                       f'reverse)')

        if ban_mentions is None:
            self.db.run_single_update_query('insert into mention_banned_users(chat_id, user_id, ban_mentions) values '
                                            '(%s, %s, 1) on duplicate key '
                                            'update ban_mentions = IF (ban_mentions, 0, 1)', (chat_id, user_id))
        else:
            self.db.run_single_update_query('insert into mention_banned_users(chat_id, user_id, ban_mentions) values '
                                            '(%s, %s, %s) on duplicate key '
                                            'update ban_mentions = %s', (chat_id, user_id, ban_mentions, ban_mentions))

    def get_all_users_ban_mention(self, chat_id: int) -> List[int]:
        """Returns list of IDs of all users that banned mentions in given chat"""
        pass

    def check_mention(self, chat_id: int, mention_id: int) -> bool:
        """Check if mention is banned in chat"""
        pass

    def check_mentions(self, chat_id: int, mentions_ids: List[int]) -> List[int]:
        """Returns list of mentions from given list that are banned in chat"""
        pass


class Sanction(Enum):
    WARNING = 0  # warning message
    MUTE_FIVE_MIN = 1  # 5-minutes mute
    MUTE_HOUR = 2  # one hour mute
    MUTE_DAY = 3  # one day mute
    BAN_MEDIA_WEEK = 4  # one week media (everything except text messages) ban
    BAN_MEDIA_MONTH = 5  # one month media (everything except text messages) ban


class ViolationsManager(metaclass=SingletonMeta):
    """Manage users' violations"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    def register_violation(self, chat_id: int, user_id: int, banned_mentions: List[int]) -> Sanction:
        """Register banned mention by user and returns sanction"""
        pass

    def forgive_violation(self, chat_id: int, user_id: int, forgiven_by: int) -> None:
        """Register user forgive somebody"""
        raise NotImplementedError('You cannot forgive people(')
