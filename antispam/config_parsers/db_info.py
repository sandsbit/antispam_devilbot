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

from os import path
from configparser import ConfigParser

from antispam.utils.singleton import SingletonMeta


class DBInfo(metaclass=SingletonMeta):
    """Parse information from db.conf"""

    blog = logging.getLogger('botlog')

    DB_CONFIG_FILE = path.join(path.dirname(path.abspath(__file__)), '../../config/db.conf')

    host: str
    port: int

    user: str
    password: str
    database: str

    def __init__(self):
        """
        Parse config file and fill all fields.

        Raise FileNotFoundError if file doesn't exist
        """

        self.blog.info('Creating new DBInfo class instance')
        self.blog.debug('Reading DB config file from : ' + path.abspath(self.DB_CONFIG_FILE))

        if not path.isfile(self.DB_CONFIG_FILE):
            msg = "Couldn't find DB config file path: " + self.DB_CONFIG_FILE
            self.blog.fatal(msg)
            raise FileNotFoundError(msg)

        app_config = ConfigParser()
        app_config.read(self.DB_CONFIG_FILE)

        self.blog.debug('Successfully read DB config file')

        self.host = app_config['GENERAL']['host']
        self.port = int(app_config['GENERAL']['port'])

        self.user = app_config['LOGIN']['user']
        self.password = app_config['LOGIN']['password']
        self.database = app_config['LOGIN']['database']
