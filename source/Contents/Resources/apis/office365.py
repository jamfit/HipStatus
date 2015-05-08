from api_exceptions import Unauthorized, NotAllowed, ServerError
import datetime
import logging
import requests


class Office365(object):
    def __init__(self, email, password, api='https://outlook.office365.com/api/v1.0'):
        self.api = api
        self.s = requests.Session()
        self.s.auth = (email, password)

    def update_auth(self, email, password):
        logging.info("Updating Office365 auth info")
        self.s.auth = (email, password)

    def me(self):
        response = self.s.get('{}/me'.format(self.api))
        _response_check(response.status_code)
        return response.json()

    def calendar_status(self, date_string):
        start = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(0, 10)
        end = start + datetime.timedelta(0, 280)
        logging.info("Reading user calendar from Office 365")
        response = self.s.get(
            '{}/me/calendarview?startdatetime={}&enddatetime={}'.format(self.api, start.strftime('%Y-%m-%dt%H:%M:%Sz'),
                                                                        end.strftime('%Y-%m-%dt%H:%M:%Sz'))
        )
        _response_check(response.status_code)
        return response.json()


def _response_check(code):
    if code != 200:
        if code == 401:
            raise Unauthorized
        elif code == 403:
            raise NotAllowed
        elif code == 500:
            raise ServerError