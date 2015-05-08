from apis import HipChat, Office365
from apis.api_exceptions import *
from AppKit import NSSecureTextField, NSMakeRect
import datetime
from Foundation import NSUserDefaults
from keychain import Keychain, KeychainValueNotFound, KeychainWriteError
import logging
from preferences import Preferences
import rumps
import threading
import time
import webbrowser

# URL to open a ticket from one of the error notifications
ticket_url = 'https://your.org/helpdesk/createticket'
hipchat_apitoken_url = 'https://your.hipchat.com/account/api'


class App(rumps.App):
    """This is the main class that runs the HipStatus app"""
    def __init__(self):
        super(App, self).__init__("HipStatus")
        self.icon = _menu_bar_icon(0)
        self.preferences = Preferences()
        self._validate_preferences()

        self.keychain = Keychain(self.preferences.email())
        self._validate_keychain()

        self.hipchat = HipChat(self.keychain.read_token())
        self.office365 = Office365(self.preferences.email(), self.keychain.read_o365())

        self.menu_pause_button = rumps.MenuItem("Pause HipStatus", self.timer_pause)
        self.menu_preferences = rumps.MenuItem('Preferences...')

        self.menu = [self.menu_pause_button, rumps.separator, self.menu_preferences, rumps.separator]

        self.menu_preferences_message = rumps.MenuItem("", self.preferences_message)
        if self.preferences.default_message():
            self.menu_preferences_message.title = self.preferences.default_message()
        else:
            self.menu_preferences_message.title = "None..."

        self.menu_preferences_email = rumps.MenuItem("Change email address", self.preferences_update_email)
        self.menu_preferences_o365 = rumps.MenuItem("Update saved Office 365 password", self.preferences_update_o365)
        self.menu_preferences_token = rumps.MenuItem("Update saved HipChat token", self.preferences_update_token)
        self.menu_preferences_get_token = rumps.MenuItem("Get your HipChat token", open_browser)

        self.menu_preferences.add(rumps.MenuItem('Status message...'))
        self.menu_preferences.add(self.menu_preferences_message)
        self.menu_preferences.add(rumps.separator)
        self.menu_preferences.add(rumps.MenuItem('Preferences...'))
        self.menu_preferences.add(self.menu_preferences_email)
        self.menu_preferences.add(self.menu_preferences_o365)
        self.menu_preferences.add(self.menu_preferences_token)
        self.menu_preferences.add(rumps.separator)
        self.menu_preferences.add(self.menu_preferences_get_token)

        self.main_timer = rumps.Timer(self.timer_trigger, 300)
        self.main_timer.start()

    def _validate_preferences(self):
        if not self.preferences.email().strip():
            logging.warning("No email address on record in preferences")
            self.preferences_update_email(None)

    def _validate_keychain(self):
        try:
            self.keychain.read_o365()
        except KeychainValueNotFound:
            logging.warning("Office 365 password not found")
            self.keychain.write_o365("Enter Password")
            self.preferences_update_o365(None, menu_call=False)

        try:
            self.keychain.read_token()
        except KeychainValueNotFound:
            logging.warning("HipChat API token not found")
            self.keychain.write_token("Enter Token")
            self.preferences_update_token(None, menu_call=False)

    @rumps.notifications
    def notification_center(self, info):
        logging.debug("Notification has been clicked")
        if 'update_o365' in info:
            self.preferences_update_o365(None)
        elif 'update_token' in info:
            self.preferences_update_token(None)
        elif 'update_email' in info:
            self.preferences_update_email(None)
        elif 'open_ticket' in info:
            webbrowser.open(info['open_ticket'])
        else:
            pass

    def preferences_message(self, sender):
        text = self.preferences.default_message()
        if text is None:
            text = ''
        prompt = rumps.Window("Leave blank to not set a status message",
                              "Enter a message to display when you are set to 'Do not disturb'", text,
                              dimensions=(275, 25))
        result = prompt.run()
        self.preferences.default_message(result.text)
        if self.preferences.default_message():
            self.menu_preferences_message.title = self.preferences.default_message()
        else:
            self.menu_preferences_message.title = "None..."

    def preferences_update_email(self, sender):
        text = self.preferences.email()
        logging.info("Prompting for new email")
        prompt = rumps.Window("", "Enter your email address", text, dimensions=(275, 25))
        result = prompt.run()
        self.preferences.email(result.text)

    def preferences_update_o365(self, sender, message="", menu_call=True):
        text = self.keychain.read_o365()
        logging.info("Prompting for Office 365 password...")
        prompt = SecureRumpsWindow(message, "Enter your Office 365 password:", text, dimensions=(275, 25))
        result = prompt.run()
        self.keychain.write_o365(result.text)
        if menu_call:
            self.office365.update_auth(self.preferences.email(), self.keychain.read_o365())

    def preferences_update_token(self, sender, message="", menu_call=True):
        text = self.keychain.read_token()
        message = "Paste your key using Ctrl+Click on the text field"
        logging.info("Prompting for HipChat API token...")
        prompt = rumps.Window(message, "Enter your HipChat API token:", text, dimensions=(375, 25))
        prompt.add_button('Get HipChat token...')
        result = prompt.run()

        if result.clicked == 2:
            open_browser()
            self.preferences_update_token(None, "Log into HipChat in the browser to copy your token, paste using "
                                          "Ctrl+Click on the text field",
                                          menu_call=menu_call)
        else:
            token = result.text
            self.keychain.write_token(token)
            if menu_call:
                self.hipchat.update_token(self.keychain.read_token())

    def timer_pause(self, sender):
        if not sender.state:
            self.icon = _menu_bar_icon(1)
            sender.title = "Resume HipStatus"
            logging.info("User has paused HipStatus")
        else:
            self.icon = _menu_bar_icon(0)
            sender.title = "Pause HipStatus"
            logging.info("User has resumed HipStatus")

        sender.state = not sender.state

    def timer_trigger(self, sender):
        now = datetime.datetime.now()
        delta = (5 - (now.minute % 5)) * 60 - now.second
        logging.debug("Timer will execute in {} seconds".format(delta))
        t = threading.Thread(target=self._update_status, args=[delta])
        t.start()

    def _update_status(self, delay):
        time.sleep(delay)
        if self.menu_pause_button.state:
            logging.info("HipStatus is paused: status will not be updated")
            return

        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            hipchat_user = self.hipchat.get_status(self.preferences.email())
        except Unauthorized:
            rumps.notification("Authentication error to HipChat",'',
                               "It looks like something may be wrong with your API token. Click here to update, or use "
                               "the 'Preferences...' menu option.",
                               data={'update_token': ''})
            return

        except UserNotFound:
            rumps.notification("Could not find the user in HipChat", self.preferences.email(),
                               "Your saved email address could not be found in HipChat. Click here to update, or use "
                               "the 'Preferences...' menu option.", data={'update_email': ''})
            return

        except (RateLimited, ServerError, ServiceUnavailable):
            rumps.notification("There seems to be a problem with HipChat", '', "There was an error indicating an issue "
                               "on HipChat's end. If the issue persists click here to open an IT Help ticket.",
                               data={'open_ticket': ticket_url})
            return

        if not hipchat_user['presence']:
            logging.info("The user is not online")
            return

        busy_hipstatus = True if hipchat_user['presence']['show'] != 'chat' else False

        try:
            office365_calendar = self.office365.calendar_status(now)
        except Unauthorized:
            rumps.notification("Authentication error to Office 365", '',
                               "Something may be wrong with your Office 365 email address/password. Click here to try "
                               "updating your password.", data={'update_o365': ''})
            return

        except ServerError:
            rumps.notification("There seems to be a problem with Office 365", '', "There was an error indicating an "
                               "issue on Office 365's end. If the issue persists click here to open an IT Help ticket.",
                               data={'open_ticket': ticket_url})
            return

        if office365_calendar['value']:
            busy_office365 = True if office365_calendar['value'][0]['ShowAs'] == 'Busy' else False
        else:
            busy_office365 = False

        if busy_hipstatus == busy_office365:
            logging.info("Status unchanged")
            return

        message = ''
        update_data = {
            'name': hipchat_user['name'],
            'email': hipchat_user['email'],
            'mention_name': hipchat_user['mention_name'],
            'title': hipchat_user['title'],
            'timezone': self.preferences.timezone(),
            'is_group_admin': hipchat_user['is_group_admin'],
            'presence': {
                'status': None,
                'show': None,
            }
        }

        if busy_hipstatus and not busy_office365:
            logging.info("Setting HipChat status to 'Available'")
            update_data['presence']['status'] = ''
            update_data['presence']['show'] = None
            message = "You are now 'Available'"

        elif busy_office365 and not busy_hipstatus:
            logging.info("Setting HipChat status to 'Do not disturb'")
            update_data['presence']['status'] = self.preferences.default_message()
            update_data['presence']['show'] = 'dnd'
            message = "You are now set to 'Do not disturb'"

        self.hipchat.update_status(update_data)
        rumps.notification("Status Updated", message, "Your status in HipChat has been updated", sound=False)


def _menu_bar_icon(run_or_pause):
    """0 for 'running' icon and 1 for 'paused' icon"""
    mode = NSUserDefaults.standardUserDefaults().stringForKey_('AppleInterfaceStyle')
    black = ['menu_bar_64_black_running.png', 'menu_bar_64_black_paused.png']
    white = ['menu_bar_64_white_running.png', 'menu_bar_64_white_paused.png']
    return white[run_or_pause] if not mode else black[run_or_pause]


def open_browser(url):
    if not url:
        url = hipchat_apitoken_url

    webbrowser.open(url)


class SecureRumpsWindow(rumps.Window):
    def __init__(self, message, title, default_text='', dimensions=(320,160)):
        super(SecureRumpsWindow, self).__init__(message, title)
        self._textfield = NSSecureTextField.alloc().initWithFrame_(NSMakeRect(0, 0, *dimensions))
        self._textfield.setSelectable_(True)
        self._alert.setAccessoryView_(self._textfield)
        self._textfield.setStringValue_(unicode(default_text))