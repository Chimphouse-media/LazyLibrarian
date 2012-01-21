from __future__ import with_statement

import os, sys, subprocess, threading, cherrypy, webbrowser, sqlite3

from lib.configobj import ConfigObj

from threading import Lock

from lazylibrarian import logger

FULL_PATH = None
PROG_DIR = None

ARGS = None
SIGNAL = None

LOGLEVEL = 1
DAEMON = False
PIDFILE= None

INIT_LOCK = Lock()
__INITIALIZED__ = False
started = False

DATADIR = None
DBFILE=None
CONFIGFILE = None
CFG = None

LOGDIR = None
LOGLIST = []

HTTP_HOST = None
HTTP_PORT = None
HTTP_USER = None
HTTP_PASS = None
HTTP_ROOT = None
HTTP_LOOK = None
LAUNCH_BROWSER = False

SAB_HOST = None
SAB_PORT = None
SAB_USER = None
SAB_PASS = None
SAB_API = None
SAB_CAT = None
SAB_DIR = None
SAB_BH = False
SAB_BHDIR = None
SAB_RET = None

def CheckSection(sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        CFG[sec] = {}
        return False

#################################################################################
## Check_setting_int                                                            #
#################################################################################
#def minimax(val, low, high):
#    """ Return value forced within range """
#    try:
#        val = int(val)
#    except:
#        val = 0
#    if val < low:
#        return low
#    if val > high:
#        return high
#    return val

################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

#################################################################################
## Check_setting_float                                                          #
#################################################################################
##def check_setting_float(config, cfg_name, item_name, def_val):
##    try:
##        my_val = float(config[cfg_name][item_name])
##    except:
##        my_val = def_val
##        try:
##            config[cfg_name][item_name] = my_val
##        except:
##            config[cfg_name] = {}
##            config[cfg_name][item_name] = my_val

##    return my_val

################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):
    try:
        my_val = config[cfg_name][item_name]
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    if log:
        logger.debug(item_name + " -> " + my_val)
    else:
        logger.debug(item_name + " -> ******")

    return my_val

def initialize():

    with INIT_LOCK:

        global __INITIALIZED__, FULL_PATH, PROG_DIR, LOGLEVEL, DAEMON, DATADIR, CONFIGFILE, CFG, LOGDIR, HTTP_HOST, HTTP_PORT, HTTP_USER, HTTP_PASS, HTTP_ROOT, HTTP_LOOK, LAUNCH_BROWSER, LOGDIR, CACHEDIR, \
            SAB_HOST, SAB_PORT, SAB_API, SAB_USER, SAB_PASS, SAB_DIR, SAB_CAT, SAB_RET, SAB_BH, SAB_BHDIR

        if __INITIALIZED__:
            return False

        CheckSection('General')
        CheckSection('SABnzbd')

        try:
            HTTP_PORT = check_setting_int(CFG, 'General', 'http_port', 5299)
        except:
            HTTP_PORT = 5299

        if HTTP_PORT < 21 or HTTP_PORT > 65535:
            HTTP_PORT = 5299

        HTTP_HOST = check_setting_str(CFG, 'General', 'http_host', '0.0.0.0')
        HTTP_USER = check_setting_str(CFG, 'General', 'http_user', '')
        HTTP_PASS = check_setting_str(CFG, 'General', 'http_pass', '')
        HTTP_ROOT = check_setting_str(CFG, 'General', 'http_root', '')
        HTTP_LOOK = check_setting_str(CFG, 'General', 'http_look', 'default')

        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'General', 'launch_browser', 1))
        LOGDIR = check_setting_str(CFG, 'General', 'logdir', '')

        SAB_HOST = check_setting_str(CFG, 'SABnzbd', 'sab_host', '')
        SAB_PORT = check_setting_str(CFG, 'SABnzbd', 'sab_port', '')
        SAB_USER = check_setting_str(CFG, 'SABnzbd', 'sab_user', '')
        SAB_PASS = check_setting_str(CFG, 'SABnzbd', 'sab_pass', '')
        SAB_API = check_setting_str(CFG, 'SABnzbd', 'sab_api', '')
        SAB_CAT = check_setting_str(CFG, 'SABnzbd', 'sab_cat', '')
        SAB_DIR = check_setting_str(CFG, 'SABnzbd', 'sab_dir', '')
        SAB_BH = bool(check_setting_int(CFG, 'SABnzbd', 'sab_bh', 0))
        SAB_BHDIR = check_setting_str(CFG, 'SABnzbd', 'sab_bhdir', '')
        SAB_RET = check_setting_str(CFG, 'SABnzbd', 'sab_ret', '')

        if not LOGDIR:
            LOGDIR = os.path.join(DATADIR, 'Logs')

        # Put the cache dir in the data dir for now
        CACHEDIR = os.path.join(DATADIR, 'cache')
        if not os.path.exists(CACHEDIR):
            try:
                os.makedirs(CACHEDIR)
            except OSError:
                logger.error('Could not create cachedir. Check permissions of: ' + DATADIR)

        # Create logdir
        if not os.path.exists(LOGDIR):
            try:
                os.makedirs(LOGDIR)
            except OSError:
                if LOGLEVEL:
                    print LOGDIR + ":"
                    print ' Unable to create folder for logs. Only logging to console.'

        # Start the logger, silence console logging if we need to
        logger.lazylibrarian_log.initLogger(loglevel=LOGLEVEL)

        # Initialize the database
        logger.info('Checking database status ...')
        try:
            dbcheck()
        except Exception, e:
            logger.error("Can't connect to the database: %s" % e)

        __INITIALIZED__ = True
        return True

def daemonize():
    """
    Fork off as a daemon
    """

    # Make a non-session-leader child process
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" %
                   (e.strerror, e.errno))

    os.setsid() #@UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2st fork failed: %s [%d]" %
                   (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if PIDFILE:
        pid = str(os.getpid())
        logger.log(u"Writing PID " + pid + " to " + str(PIDFILE))
        file(PIDFILE, 'w').write("%s\n" % pid)

def launch_browser(host, port, root):
    if host == '0.0.0.0':
        host = 'localhost'

    try:
        webbrowser.open('http://%s:%i%s' % (host, port, root))
    except Exception, e:
        logger.error('Could not launch browser: %s' % e)

def config_write():
    new_config = ConfigObj()
    new_config.filename = CONFIGFILE

    new_config['General'] = {}
    new_config['General']['http_port'] = HTTP_PORT
    new_config['General']['http_host'] = HTTP_HOST
    new_config['General']['http_user'] = HTTP_USER
    new_config['General']['http_pass'] = HTTP_PASS
    new_config['General']['http_root'] = HTTP_ROOT
    new_config['General']['http_look'] = HTTP_LOOK
    new_config['General']['launch_browser'] = int(LAUNCH_BROWSER)
    new_config['General']['logdir'] = LOGDIR

    new_config['SABnzbd'] = {}
    new_config['SABnzbd']['sab_host'] = SAB_HOST
    new_config['SABnzbd']['sab_port'] = SAB_PORT
    new_config['SABnzbd']['sab_user'] = SAB_USER
    new_config['SABnzbd']['sab_pass'] = SAB_PASS
    new_config['SABnzbd']['sab_api'] = SAB_API
    new_config['SABnzbd']['sab_cat'] = SAB_CAT
    new_config['SABnzbd']['sab_dir'] = SAB_DIR
    new_config['SABnzbd']['sab_bh'] = int(SAB_BH)
    new_config['SABnzbd']['sab_bhdir'] = SAB_BHDIR
    new_config['SABnzbd']['sab_ret'] = SAB_RET

    new_config.write()

def dbcheck():

    conn=sqlite3.connect(DBFILE)
    c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS authors (AuthorID TEXT UNIQUE, AuthorName TEXT, AuthorImgs TEXT, AuthorImgl TEXT, AuthorLink TEXT, DateAdded TEXT, Status TEXT, LatestBook TEXT, ReleaseDate TEXT, HaveBooks INTEGER, TotalBooks INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS books (AuthorID TEXT, AuthorName TEXT, AuthorLink TEXT, BookName TEXT, BookIsbn TEXT, BookRate INTEGER, BookImgs TEXT, BookImgl TEXT, BookPages INTEGER, BookLink TEXT, BookID TEXT UNIQUE, ReleaseDate TEXT, DateAdded TEXT, Status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS snatched (BookID TEXT, BookName TEXT, Size INTEGER, URL TEXT, DateAdded TEXT, Status TEXT, FolderName TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS have (AuthorName TEXT, BookName TEXT)')

    try:
        c.execute('SELECT BookID from authors')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE authors ADD COLUMN BookID TEXT')

    try:
        c.execute('SELECT HaveBooks from authors')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE authors ADD COLUMN HaveBooks INTEGER DEFAULT 0')

    try:
        c.execute('SELECT TotalBooks from authors')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE authors ADD COLUMN TotalBooks INTEGER DEFAULT 0')

    try:
        c.execute('SELECT FolderName from snatched')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE snatched ADD COLUMN FolderName TEXT')

    conn.commit()
    c.close()

def start():
    global __INITIALIZED__, started

    if __INITIALIZED__:
        # Crons and scheduled jobs go here
        started = True

def shutdown(restart=False):
    config_write()
    cherrypy.engine.exit()

    if PIDFILE :
        logger.info('Removing pidfile %s' % PIDFILE)
        os.remove(PIDFILE)

    if restart:
        logger.info('LazyLibrarian is restarting ...')
        popen_list = [sys.executable, FULL_PATH]
        popen_list += ARGS
        if '--nolaunch' not in popen_list:
            popen_list += ['--nolaunch']
            logger.info('Restarting Headphones with ' + str(popen_list))
        subprocess.Popen(popen_list, cwd=os.getcwd())



    os._exit(0)
