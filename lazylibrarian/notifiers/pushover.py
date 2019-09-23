# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/lazylibrarian/
#
# This file is part of LazyLibrarian.
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


from lib.six import PY2
# noinspection PyUnresolvedReferences
from lib.six.moves.urllib_parse import urlencode
# noinspection PyUnresolvedReferences
from lib.six.moves.http_client import HTTPSConnection

import lazylibrarian
from lazylibrarian import logger
from lazylibrarian.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD
from lazylibrarian.formatter import unaccented


class PushoverNotifier:

    def __init__(self):
        pass

    @staticmethod
    def _sendPushover(message=None, event=None, pushover_apitoken=None, pushover_keys=None,
                      pushover_device=None, notificationType=None, method=None, force=False):

        if not lazylibrarian.CONFIG['USE_PUSHOVER'] and not force:
            return False

        if pushover_apitoken is None:
            pushover_apitoken = lazylibrarian.CONFIG['PUSHOVER_APITOKEN']
        if pushover_keys is None:
            pushover_keys = lazylibrarian.CONFIG['PUSHOVER_KEYS']
        if pushover_device is None:
            pushover_device = lazylibrarian.CONFIG['PUSHOVER_DEVICE']
        if method is None:
            method = 'POST'
        if notificationType is None:
            testMessage = True
            uri = "/1/users/validate.json"
            logger.debug("Testing Pushover authentication and retrieving the device list.")
        else:
            testMessage = False
            uri = "/1/messages.json"
        logger.debug("Pushover event: " + str(event))
        logger.debug("Pushover message: " + str(message))
        logger.debug("Pushover api: " + str(pushover_apitoken))
        logger.debug("Pushover keys: " + str(pushover_keys))
        logger.debug("Pushover device: " + str(pushover_device))
        logger.debug("Pushover notification type: " + str(notificationType))

        http_handler = HTTPSConnection('api.pushover.net')

        if PY2:
            message = message.encode(lazylibrarian.SYS_ENCODING)
            event = event.encode(lazylibrarian.SYS_ENCODING)
        try:
            data = {'token': pushover_apitoken,
                    'user': pushover_keys,
                    'title': event,
                    'message': message,
                    'device': pushover_device,
                    'priority': lazylibrarian.CONFIG['PUSHOVER_PRIORITY']}
            http_handler.request(method,
                                 uri,
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
            pass
        except Exception as e:
            logger.error(str(e))
            return False

        response = http_handler.getresponse()
        request_body = response.read()
        request_status = response.status
        logger.debug("Pushover Response: %s" % request_status)
        logger.debug("Pushover Reason: %s" % response.reason)

        if request_status == 200:
            if testMessage:
                logger.debug(request_body)
                if 'devices' in request_body:
                    return "Devices: %s" % request_body.split('[')[1].split(']')[0]
                else:
                    return request_body
            else:
                return True
        elif 400 <= request_status < 500:
            logger.error("Pushover request failed: %s" % str(request_body))
            return False
        else:
            logger.error("Pushover notification failed: %s" % request_status)
            return False

    def _notify(self, message=None, event=None, pushover_apitoken=None, pushover_keys=None,
                pushover_device=None, notificationType=None, method=None, force=False):
        """
        Sends a pushover notification based on the provided info or LL config

        title: The title of the notification to send
        message: The message string to send
        username: The username to send the notification to (optional, defaults to the username in the config)
        force: If True then the notification will be sent even if pushover is disabled in the config
        """
        try:
            message = unaccented(message)
        except Exception as e:
            logger.warn("Pushover: could not convert  message: %s" % e)
        # suppress notifications if the notifier is disabled but the notify options are checked
        if not lazylibrarian.CONFIG['USE_PUSHOVER'] and not force:
            return False

        logger.debug("Pushover: Sending notification " + str(message))

        return self._sendPushover(message, event, pushover_apitoken, pushover_keys,
                                  pushover_device, notificationType, method, force)

#
# Public functions
#

    def notify_snatch(self, title):
        if lazylibrarian.CONFIG['PUSHOVER_ONSNATCH']:
            self._notify(message=title, event=notifyStrings[NOTIFY_SNATCH], notificationType='note')

    def notify_download(self, title):
        if lazylibrarian.CONFIG['PUSHOVER_ONDOWNLOAD']:
            self._notify(message=title, event=notifyStrings[NOTIFY_DOWNLOAD], notificationType='note')

    def test_notify(self, title="Test"):
        res = self._notify(message="This notification asks for the device list",
                           event=title, notificationType=None, force=True)
        if res:
            _ = self._notify(message="This is a test notification from LazyLibrarian",
                             event=title, notificationType='note', force=True)
        return res

    def update_library(self, showName=None):
        pass


notifier = PushoverNotifier
