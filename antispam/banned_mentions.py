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
import datetime

from typing import Optional, List
from enum import Enum

from antispam.utils.singleton import SingletonMeta
from antispam.utils.db import DBUtils


class MentionBanManager(metaclass=SingletonMeta):
    """Manage users that ban their mentions"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    def set_user_ban_mention(self, chat_id: int, user_id: int, ban_mentions: Optional[bool] = None) -> bool:
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

        return self.db.run_single_query('select ban_mentions from mention_banned_users '
                                        'where user_id = %s and chat_id = %s', (user_id, chat_id))[0][0]

    def get_all_users_ban_mention(self, chat_id: int) -> List[int]:
        """Returns list of IDs of all users that banned mentions in given chat"""

        self.blog.info(f'Getting all ban_mentions users in chat #{chat_id}')

        return list(map(lambda x: x[0], self.db.run_single_query('select user_id from mention_banned_users '
                                                                 'where chat_id = %s and ban_mentions = 1', [chat_id])))

    def check_mention(self, chat_id: int, mention_id: int) -> bool:
        """Check if mention is banned in chat"""
        self.blog.debug(f'Checking #{mention_id} mention in chat #{chat_id}')

        return len(self.db.run_single_query('select * from mention_banned_users '
                                            'where chat_id = %s and user_id = %s and ban_mentions = 1',
                                            (chat_id, mention_id))) != 0

    def check_mentions(self, chat_id: int, mentions_ids: List[int]) -> List[int]:
        """Returns list of mentions from given list that are banned in chat"""
        res = []

        for id_ in mentions_ids:
            if self.check_mention(chat_id, id_):
                res += [id_]

        return res


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

    def _get_sanction_for_user(self, chat_id: int, user_id: int) -> List[Sanction]:
        """Get sanction for given user in given chat"""

        self.blog.info(f'Getting sanction for user #{user_id} in chat #{chat_id}')

        user_info = self.db.run_single_query('select violations_today, violations_month from violations '
                                             'where chat_id = %s and user_id = %s', (chat_id, user_id))

        if len(user_info) == 0:
            raise RuntimeError(f'No such user with id {user_id}')

        violations_today, violations_month = user_info[0]

        sanctions = []

        if violations_month == 1:
            sanctions.append(Sanction.WARNING)
        elif violations_today <= 2 and violations_month < 10:
            sanctions.append(Sanction.MUTE_FIVE_MIN)
        elif (violations_today <= 2 and violations_month >= 10) or (violations_today <= 5 and violations_month < 30):
            sanctions.append(Sanction.MUTE_HOUR)
        else:
            sanctions.append(Sanction.MUTE_DAY)

        if violations_today == 5 or violations_month > 30:
            sanctions.append(Sanction.BAN_MEDIA_WEEK)
        elif violations_month > 50:
            sanctions.append(Sanction.BAN_MEDIA_MONTH)

        return sanctions

    def register_violation(self, chat_id: int, user_id: int, banned_mentions: List[int]) -> List[Sanction]:
        """Register banned mention by user and returns sanction"""

        self.blog.info(f'Registering violation for user #{user_id} in chat #{chat_id}')

        today = datetime.datetime.utcnow().date()

        banned_mentions_str = ','.join(map(str, banned_mentions))

        user_today_query = self.db.run_single_query('select today from violations where chat_id = %s and user_id = %s',
                                                    (chat_id, user_id))
        if len(user_today_query) == 0:
            self.db.run_single_update_query(f'insert into violations(chat_id, user_id, today, violations_today, '
                                            f'violations_month, violations, last_violation_against) '
                                            f'values (%s, %s, %s, 1, 1, 1, %s)',
                                            (chat_id, user_id, today, banned_mentions_str))
        else:
            today_user = user_today_query[0][0]

            if today_user == today:
                self.db.run_single_update_query('update violations set last_violation_against = %s, '
                                                'violations_today = violations_today + 1, '
                                                'violations_month = violations_month + 1,'
                                                'violations = violations + 1 where user_id = %s '
                                                'and chat_id = %s', (banned_mentions_str, user_id, chat_id))
            elif today.month == today_user.month:
                self.db.run_single_update_query('update violations set last_violation_against = %s, '
                                                'today = %s, violations_today = 1, '
                                                'violations_month = violations_month + 1,'
                                                'violations = violations + 1 where user_id = %s '
                                                'and chat_id = %s', (banned_mentions_str, today, user_id, chat_id))
            else:
                self.db.run_single_update_query('update violations set last_violation_against = %s, '
                                                'today = %s, violations_today = 1, '
                                                'violations_month = 1,'
                                                'violations = violations + 1 where user_id = %s '
                                                'and chat_id = %s', (banned_mentions_str, today, user_id, chat_id))

        return self._get_sanction_for_user(chat_id, user_id)

    def forgive_violation(self, chat_id: int, user_id: int, forgiven_by: int) -> None:
        """Register user forgive somebody"""
        raise NotImplementedError('You cannot forgive people(')
