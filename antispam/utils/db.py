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

from typing import Dict, List, Tuple, Any
from pprint import pformat

import mysql.connector

from mysql.connector import MySQLConnection
from mysql.connector.errors import DatabaseError

from antispam.config_parsers.db_info import DBInfo
from antispam.utils.singleton import SingletonMeta


class DBUtils(metaclass=SingletonMeta):

    blog = logging.getLogger('botlog')

    _botdb: Dict[int, MySQLConnection] = {}

    def __init__(self) -> None:
        """
        Init global botdb variable with new MySql connection at id 0.
        """
        self.setup_new_connection()

    def setup_new_connection(self, connection_id: int = 0):
        self.blog.info(f'Initializing database managing connection with id {connection_id}')
        SingletonMeta._instances_lock.release()
        dbi = DBInfo()
        SingletonMeta._instances_lock.acquire()

        self._botdb[connection_id] = mysql.connector.connect(
            host=dbi.host,
            port=dbi.port,
            user=dbi.user,
            password=dbi.password,
            database=dbi.database
        )

        self.blog.info(f'Connected to database on {dbi.user}@{dbi.host}:{dbi.port} with id = {connection_id} successfully')

        self.run_single_update_query('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')

        self.blog.debug(f'Set MySql session (id = {connection_id})  transaction isolation level to READ UNCOMMITTED')

    def run_single_query(self, operation: str, params=(), connection_id: int = 0) -> List[Tuple[Any]]:
        """
        Run SELECT query to db that don't update DB. Use run_single_update_query
        if your query updated DB.
        Arguments will be passed to MySQLCursor.execute().

        ProgrammingError will be raised on error.

        Consider using 'params' argument instead of others string building methods
        to avoid SQL injections. You can report SQL injections problems found in
        the project at https://github.com/sandsbit/skarmabot/security/advisories/new.
        TODO: remove bad link
        """
        self.blog.debug('Running single SELECT query: ' + operation + 'with params: ' + pformat(params))

        if connection_id not in self._botdb:
            msg = f"There's no connection with id #{connection_id}"
            self.blog.error(msg)
            raise DatabaseError(msg)

        cursor_ = self._botdb[connection_id].cursor()
        cursor_.execute(operation, params)

        res_ = cursor_.fetchall()

        self.blog.debug(f'Got {cursor_.rowcount} rows in response')

        cursor_.close()
        return res_

    def run_single_update_query(self, operation: str, params=(), connection_id: int = 0) -> None:
        """
        Run query to db that do update DB. Use run_single_query instead
        if you are doing SELECT query .
        Arguments will be passed to MySQLCursor.execute().

        ProgrammingError will be raised on error.

        Consider using 'params' argument instead of others string building methods
        to avoid SQL injections. You can report SQL injections problems found in
        the project at https://github.com/sandsbit/skarmabot/security/advisories/new.
        TODO: remove bad link
        """
        self.blog.debug('Running single NOT select query: ' + operation + 'with params: ' + pformat(params))

        if connection_id not in self._botdb:
            msg = f"There's no connection with id #{connection_id}"
            self.blog.error(msg)
            raise DatabaseError(msg)

        cursor_ = self._botdb[connection_id].cursor()
        cursor_.execute(operation, params)

        self._botdb[connection_id].commit()
        cursor_.close()

    def is_connected(self, connection_id: int = 0) -> bool:
        return self._botdb[connection_id].is_connected()

