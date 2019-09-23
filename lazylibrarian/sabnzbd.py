#  This file is part of Lazylibrarian.
#  Lazylibrarian is free software':'you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  Lazylibrarian is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with Lazylibrarian.  If not, see <http://www.gnu.org/licenses/>.


try:
    import urllib3
    import requests
except ImportError:
    import lib.requests as requests

import lazylibrarian
from lazylibrarian import logger
from lazylibrarian.common import proxyList
from lazylibrarian.formatter import check_int, unaccented_str
# noinspection PyUnresolvedReferences
from lib.six.moves.urllib_parse import urlencode


def checkLink():
    # connection test, check host/port
    auth, _ = SABnzbd(nzburl='auth')
    if not auth:
        return "Unable to talk to SABnzbd, check HOST/PORT/SUBDIR"
    # check apikey is valid
    cats, _ = SABnzbd(nzburl='get_cats')  # type: dict
    if not cats:
        return "Unable to talk to SABnzbd, check APIKEY"
    # check category exists
    if lazylibrarian.CONFIG['SAB_CAT']:
        if 'categories' not in cats or not len(cats['categories']):
            return "SABnzbd seems to have no categories set"
        if lazylibrarian.CONFIG['SAB_CAT'] not in cats['categories']:
            return "SABnzbd: Unknown category [%s]\nValid categories:\n%s" % (
                    lazylibrarian.CONFIG['SAB_CAT'], str(cats['categories']))
    return "SABnzbd connection successful"


def SABnzbd(title=None, nzburl=None, remove_data=False):

    if nzburl in ['delete', 'delhistory'] and title == 'unknown':
        res = '%s function unavailable in this version of sabnzbd, no nzo_ids' % nzburl
        logger.debug(res)
        return False, res

    hostname = lazylibrarian.CONFIG['SAB_HOST']
    port = check_int(lazylibrarian.CONFIG['SAB_PORT'], 0)
    if not hostname or not port:
        res = 'Invalid sabnzbd host or port, check your config'
        logger.error(res)
        return False, res

    if hostname.endswith('/'):
        hostname = hostname[:-1]
    if not hostname.startswith("http://") and not hostname.startswith("https://"):
        hostname = 'http://' + hostname

    HOST = "%s:%s" % (hostname, port)

    if lazylibrarian.CONFIG['SAB_SUBDIR']:
        HOST = HOST + "/" + lazylibrarian.CONFIG['SAB_SUBDIR']

    params = {}
    if nzburl == 'auth' or nzburl == 'get_cats':
        # connection test, check auth mode or get_cats
        params['mode'] = nzburl
        params['output'] = 'json'
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        title = 'LL.(%s)' % nzburl
    elif nzburl == 'queue':
        params['mode'] = 'queue'
        params['limit'] = '100'
        params['output'] = 'json'
        if lazylibrarian.CONFIG['SAB_USER']:
            params['ma_username'] = lazylibrarian.CONFIG['SAB_USER']
        if lazylibrarian.CONFIG['SAB_PASS']:
            params['ma_password'] = lazylibrarian.CONFIG['SAB_PASS']
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        title = 'LL.(Queue)'
    elif nzburl == 'history':
        params['mode'] = 'history'
        params['limit'] = '100'
        params['output'] = 'json'
        if lazylibrarian.CONFIG['SAB_USER']:
            params['ma_username'] = lazylibrarian.CONFIG['SAB_USER']
        if lazylibrarian.CONFIG['SAB_PASS']:
            params['ma_password'] = lazylibrarian.CONFIG['SAB_PASS']
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        title = 'LL.(History)'
    elif nzburl == 'delete':
        # only deletes tasks if still in the queue, ie NOT completed tasks
        params['mode'] = 'queue'
        params['output'] = 'json'
        params['name'] = nzburl
        params['value'] = title
        if lazylibrarian.CONFIG['SAB_USER']:
            params['ma_username'] = lazylibrarian.CONFIG['SAB_USER']
        if lazylibrarian.CONFIG['SAB_PASS']:
            params['ma_password'] = lazylibrarian.CONFIG['SAB_PASS']
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        if remove_data:
            params['del_files'] = 1
        title = 'LL.(Delete) ' + title
    elif nzburl == 'delhistory':
        params['mode'] = 'history'
        params['output'] = 'json'
        params['name'] = 'delete'
        params['value'] = title
        if lazylibrarian.CONFIG['SAB_USER']:
            params['ma_username'] = lazylibrarian.CONFIG['SAB_USER']
        if lazylibrarian.CONFIG['SAB_PASS']:
            params['ma_password'] = lazylibrarian.CONFIG['SAB_PASS']
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        if remove_data:
            params['del_files'] = 1
        title = 'LL.(DelHistory) ' + title
    else:
        params['mode'] = 'addurl'
        params['output'] = 'json'
        if nzburl:
            params['name'] = nzburl
        if title:
            params['nzbname'] = title
        if lazylibrarian.CONFIG['SAB_USER']:
            params['ma_username'] = lazylibrarian.CONFIG['SAB_USER']
        if lazylibrarian.CONFIG['SAB_PASS']:
            params['ma_password'] = lazylibrarian.CONFIG['SAB_PASS']
        if lazylibrarian.CONFIG['SAB_API']:
            params['apikey'] = lazylibrarian.CONFIG['SAB_API']
        if lazylibrarian.CONFIG['SAB_CAT']:
            params['cat'] = lazylibrarian.CONFIG['SAB_CAT']
        if lazylibrarian.CONFIG['USENET_RETENTION']:
            params["maxage"] = lazylibrarian.CONFIG['USENET_RETENTION']

# FUTURE-CODE
#    if lazylibrarian.SAB_PRIO:
#        params["priority"] = lazylibrarian.SAB_PRIO
#    if lazylibrarian.SAB_PP:
#        params["script"] = lazylibrarian.SAB_SCRIPT

    URL = HOST + "/api?" + urlencode(params)

    # to debug because of api
    if lazylibrarian.LOGLEVEL & lazylibrarian.log_dlcomms:
        logger.debug('Request url for <a href="%s">SABnzbd</a>' % URL)
    proxies = proxyList()
    try:
        timeout = check_int(lazylibrarian.CONFIG['HTTP_TIMEOUT'], 30)
        r = requests.get(URL, timeout=timeout, proxies=proxies)
        result = r.json()
    except requests.exceptions.Timeout:
        res = "Timeout connecting to SAB with URL: %s" % URL
        logger.error(res)
        return False, res
    except Exception as e:
        if hasattr(e, 'reason'):
            errmsg = e.reason
        elif hasattr(e, 'strerror'):
            errmsg = e.strerror
        else:
            errmsg = str(e)

        res = "Unable to connect to SAB with URL: %s, %s" % (URL, errmsg)
        logger.error(res)
        return False, res
    if lazylibrarian.LOGLEVEL & lazylibrarian.log_dlcomms:
        logger.debug("Result text from SAB: " + str(result))

    if title:
        title = unaccented_str(title)
        if title.startswith('LL.('):
            return result, ''
    if result['status'] is True:
        logger.info("%s sent to SAB successfully." % title)
        # sab versions earlier than 0.8.0 don't return nzo_ids
        if 'nzo_ids' in result:
            if result['nzo_ids']:  # check its not empty
                return result['nzo_ids'][0], ''
        return 'unknown'
    elif result['status'] is False:
        res = "SAB returned Error: %s" % result['error']
        logger.error(res)
        return False, res
    else:
        res = "Unknown error: %s" % str(result)
        logger.error(res)
        return False, res
