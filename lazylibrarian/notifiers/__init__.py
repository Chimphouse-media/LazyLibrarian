# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from . import androidpn
from . import boxcar
from . import custom_notify
from . import email_notify
from . import nma
from . import prowl
from . import growl
from . import pushbullet
from . import pushover
from . import slack
from . import tweet
from . import telegram
from lazylibrarian import logger

# online
twitter_notifier = tweet.TwitterNotifier()
boxcar_notifier = boxcar.BoxcarNotifier()
pushbullet_notifier = pushbullet.PushbulletNotifier()
pushover_notifier = pushover.PushoverNotifier()
androidpn_notifier = androidpn.AndroidPNNotifier()
prowl_notifier = prowl.Prowl_Notifier()
growl_notifier = growl.Growl_Notifier()
nma_notifier = nma.NMA_Notifier()
slack_notifier = slack.SlackNotifier()
email_notifier = email_notify.EmailNotifier()
telegram_notifier = telegram.Telegram_Notifier()
#
custom_notifier = custom_notify.CustomNotifier()

notifiers = [
    twitter_notifier,
    boxcar_notifier,
    pushbullet_notifier,
    pushover_notifier,
    androidpn_notifier,
    prowl_notifier,
    growl_notifier,
    nma_notifier,
    slack_notifier,
    email_notifier,
    telegram_notifier
]


def custom_notify_download(bookid):
    try:
        custom_notifier.notify_download(bookid)
    except Exception as e:
        logger.warn('Custom notify download failed: %s' % str(e))


def custom_notify_snatch(bookid):
    try:
        custom_notifier.notify_snatch(bookid)
    except Exception as e:
        logger.warn('Custom notify snatch failed: %s' % str(e))


def notify_download(title, bookid=None):
    try:
        for n in notifiers:
            if 'EmailNotifier' in str(n):
                n.notify_download(title, bookid=bookid)
            else:
                n.notify_download(title)
    except Exception as e:
        logger.warn('Notify download failed: %s' % str(e))


def notify_snatch(title):
    try:
        for n in notifiers:
            n.notify_snatch(title)
    except Exception as e:
        logger.warn('Notify snatch failed: %s' % str(e))
