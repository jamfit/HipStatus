import biplist
import datetime
import logging
import os
from SystemConfiguration import SCDynamicStoreCopyConsoleUser


def user_info():
    """Returns the logged in username and their home directory"""
    username = SCDynamicStoreCopyConsoleUser(None, None, None)[0]
    user_home = os.path.expanduser('~{}'.format(username))
    return username, user_home


class Preferences():
    def __init__(self):
        user, home = user_info()
        self._plist_path = '{}/Library/Preferences/com.jamfsw.hipstatus.plist'.format(home)
        try:
            prefs = biplist.readPlist(self._plist_path)
        except IOError:
            logging.error("No com.jamfsw.hipstatus preferences file found")
            apple_reference = datetime.date(2001, 1, 1).strftime("%Y-%m-%d %H:%M:%S")
            prefs = {'email': '', 'default_message': '', 'pause_until': apple_reference}
            self._save_default(prefs)

        self._plist = prefs

    def _save_default(self, root):
        logging.info("Writing default com.jamfsw.hipstatus preferences file")
        biplist.writePlist(root, self._plist_path)

    def _change_preference(self, name, data):
        if not data:
            try:
                return self._plist[name]
            except KeyError:
                return

        else:
            logging.info("Setting new '{}': {}".format(name, data))
            self._plist[name] = data
            self.update()
            return

    @staticmethod
    def timezone():
        # This will return a timezone abbreviation: e.g. 'CDT'
        # time.tzname[time.localtime().tm_isdst]
        # HipChat requires a full timezone name: America/Chicago
        return os.readlink('/etc/localtime').split('zoneinfo/')[-1]

    def update(self):
        logging.info("Updating com.jamfsw.hipstatus preferences file")
        biplist.writePlist(self._plist, self._plist_path)

    def email(self, new_email=None):
        return self._change_preference('email', new_email)

    def default_message(self, new_message=None):
        return self._change_preference('default_message', new_message)

    def pause_until(self, date_string=None):
        return self._change_preference('pause_until', date_string)