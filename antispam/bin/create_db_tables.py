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

"""
This file contains functions that create empty DB
tables for project. Run this file to create it
automatically.
"""

from typing import List, Callable

from mysql.connector.errors import DatabaseError

from antispam.utils.db import DBUtils


def create_error_table(dbu: DBUtils):
    tables = dbu.run_single_query("SHOW TABLES;")
    if tuple('errors') in tables:
        raise DatabaseError("Table 'errors' already exists")

    dbu.run_single_update_query("""create table errors
                               (
                                 id int auto_increment,
                                 name text not null,
                                 stacktrace longtext null,
                                 constraint errors_pk
                                  primary key (id)
                               );""")


def create_chats_table(dbu: DBUtils):
    tables = dbu.run_single_query("SHOW TABLES;")
    if tuple('chats') in tables:
        raise DatabaseError("Table 'chats' already exists")

    dbu.run_single_update_query("""create table chats
                                   (
                                        id int auto_increment,
                                        chat_id text not null,
                                        constraint chats_pk
                                            primary key (id)
                                   );

""")


def create_announcements_table(dbu: DBUtils):
    tables = dbu.run_single_query("SHOW TABLES;")
    if tuple('announcements') in tables:
        raise DatabaseError("Table 'announcements' already exists")

    dbu.run_single_update_query("""create table announcements
                                   (
                                     id int auto_increment,
                                     text longtext not null,
                                     constraint announcements_pk
                                      primary key (id)
                                   );""")


def _run_functions_and_print_db_errors(functions: List[Callable[[DBUtils], None]], dbu: DBUtils):
    for fun in functions:
        try:
            fun(dbu)
        except DatabaseError as e:
            print(e.msg)


if __name__ == '__main__':
    dbu = DBUtils()

    _run_functions_and_print_db_errors([create_error_table,
                                        create_chats_table, create_announcements_table], dbu)
    print('Done.')
