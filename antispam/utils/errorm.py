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

import traceback
import logging
import pprint

from functools import wraps
from typing import List, Tuple

from mysql.connector.errors import DatabaseError

from antispam.utils.singleton import SingletonMeta
from antispam.utils.db import DBUtils
from antispam.utils import email_utils
from antispam.config_parsers.email_info import EmailInfo


class ErrorManager(metaclass=SingletonMeta):
    """
    Manage errors and exceptions.

    Errors are stored in 'errors' table in DB.
    """

    blog = logging.getLogger('botlog')

    _dbu: DBUtils = DBUtils()

    report_by_email = True

    def get_all_errors(self) -> List[Tuple[int, str, str]]:
        """Get list of all reported errors from DB"""

        return self._dbu.run_single_query('select * from errors')

    def report_error(self, name: str, stacktrace: str) -> None:
        """Report new error to DB"""
        self.blog.info('Reporting new error: ' + name)
        self._dbu.run_single_update_query('insert into skarma.errors (name, stacktrace) VALUES (%s, %s)', (name, stacktrace))

        if self.report_by_email:
            try:
                self._report_via_email(name, stacktrace)
            except Exception as e:
                self.blog.exception(e)
                self.report_by_email = False
                self.report_exception(e)

    def report_exception(self, e: Exception) -> None:
        """Report new error to DB"""
        self.report_error(repr(e), ' '.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))

    def get_number_of_errors(self) -> int:
        """Returns number of reported errors in DB"""
        res_ = self._dbu.run_single_query("select count(*) from errors")

        if len(res_) != 1 or (len(res_[0]) != 1) or type(res_[0][0]) is not int:
            msg = 'Invalid response from DB (getting number of errors): ' + pprint.pformat(res_)
            self.blog.error(msg)
            raise DatabaseError(msg)

        return res_[0][0]

    def clear_all_errors(self) -> None:
        """Clear all reported errors from database"""
        self.blog.debug('Removing all errors from DB')

        self._dbu.run_single_update_query('delete from errors')

    @staticmethod
    def _report_via_email(name: str, stacktrace: str) -> None:
        """Send error report to email. See email.conf for more information"""
        email_utils.send_email(EmailInfo().user_to, 'Error in SKarma: ' + name, stacktrace)  # TODO: Replce name


def catch_error(f):
    """
    Catches errors in handlers.

    Thanks to https://github.com/Lanseuo!
    See https://github.com/python-telegram-bot/python-telegram-bot/issues/855 for more information
    """

    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.getLogger('botlog').exception(e)
            ErrorManager().report_exception(e)

    return wrap
