from api_exceptions import Unauthorized, NotAllowed, UserNotFound, RateLimited, ServerError, ServiceUnavailable
import json
import logging
import requests


class HipChat(object):
    def __init__(self, token, api='https://api.hipchat.com/v2'):
        self.api = api
        self.default_headers = {'content-type': 'application/json', 'Authorization': 'Bearer {}'.format(token)}

    def update_token(self, token):
        logging.info("Updating HipChat API token")
        self.default_headers['Authorization'] = 'Bearer {}'.format(token)

    def get_status(self, email):
        response = requests.get('{}/user/{}'.format(self.api, email), headers=self.default_headers)
        _response_check(response.status_code)
        return response.json()

    def update_status(self, data):
        logging.debug(data)
        email = data['email']
        response = requests.put('{}/user/{}'.format(self.api, email), data=json.dumps(data),
                                headers=self.default_headers)
        _response_check(response.status_code)


def _response_check(code):
    if code not in (200, 204):
        if code == 401:
            raise Unauthorized
        elif code == 403:
            raise NotAllowed
        elif code == 404:
            raise UserNotFound
        elif code == 429:
            raise RateLimited
        elif code == 500:
            raise ServerError
        elif code == 503:
            raise ServiceUnavailable