import keyring
from keyring.errors import PasswordSetError
import logging


class Keychain(object):
    def __init__(self, email):
        self.email = email

    def read_o365(self):
        logging.debug("Reading Office 365 password from user's keychain")
        return self._read_keychain('com.jamfsw.hipstatus.o365')

    def read_token(self):
        logging.debug("Reading HipChat API token from user's keychain")
        return self._read_keychain('com.jamfsw.hipstatus.hctoken')

    def _read_keychain(self, service):
        value = keyring.get_password(service, self.email)
        if not value:
            raise KeychainValueNotFound('Value not found in the keychain for: {}, {}'.format(service, self.email))

        return value

    def write_o365(self, passwd):
        logging.debug("Writing Office 365 password to user's keychain")
        keyring.set_password('com.jamfsw.hipstatus.o365', self.email, passwd)

    def write_token(self, token):
        logging.debug("Writing HipChat token to user's keychain")
        keyring.set_password('com.jamfsw.hipstatus.hctoken', self.email, token)

    def _write_to_keychain(self, service, passwd):
        try:
            keyring.set_password(service, self.email, passwd)
        except PasswordSetError:
            raise KeychainWriteError('Unable to write value to keychain: the keychain may be locked')


class KeychainValueNotFound(Exception):
    pass


class KeychainWriteError(Exception):
    pass