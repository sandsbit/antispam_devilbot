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

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from antispam.config_parsers.email_info import EmailInfo


def send_email(to: str, subject: str, content: str):
    """Send email from email that is configured in email.conf"""

    blog = logging.getLogger('botlog')
    blog.info(f'Sending email "{subject}" to {to}')

    emi = EmailInfo()

    message = MIMEMultipart()
    message['From'] = emi.send_from
    message['To'] = to
    message['Subject'] = subject

    message.attach(MIMEText(content, 'plain'))

    blog.debug('Sending email: ended creating message')

    session = SMTP(emi.smtp_host, emi.smtp_port)
    session.starttls()
    session.login(emi.user, emi.password)

    blog.debug('Sending email: created SMTP session')

    body = message.as_string()
    session.sendmail(emi.send_from, to, body)

    blog.debug('Email successfully sent')
