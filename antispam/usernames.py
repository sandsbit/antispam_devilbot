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

from mysql.connector.errors import DatabaseError

from antispam.utils.db import DBUtils
from antispam.utils.singleton import SingletonMeta


class NoSuchUser(Exception):
    pass


class UsernamesManager(metaclass=SingletonMeta):
    """Associate user's id with username"""

    blog = logging.getLogger('botlog')
    db: DBUtils = DBUtils()

    user_names = dict()

    def __init__(self):
        """Load usernames table from database"""

        self.blog.debug('Creating UsernamesManager instance')

        result = self.db.run_single_query('select user_id, name from usernames')

        self.user_names = dict(map(lambda x: (int(x[0]), x[1]), result))

    def get_username_by_id(self, id_: int) -> str:
        """Get user's name from database by his id. NoSuchUser will be thrown if there is no such user id in database"""

        self.blog.info(f'Getting username of user with id #{id_}')

        if id_ in self.user_names:
            return self.user_names[id_]
        else:
            raise NoSuchUser

    def set_username(self, id_: int, name: str) -> None:
        """Set name of user with given id"""

        self.blog.info(f'Setting username of user with id #{id_} to "{name}"')

        if self.user_names.get(id_, '') is not name:
            self.db.run_single_update_query('insert into usernames (user_id, name) values (%(id)s, %(name)s) '
                                            'on duplicate key update name = %(name)s', {'id': id_, 'name': name})
            self.user_names[id_] = name
