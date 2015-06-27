import json
import ssl
import base64
import sys

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from quickpay import exceptions
import quickpay


class QPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)


class QPApi(object):
    api_version = '10'
    base_url = 'https://api.quickpay.net'

    def __init__(self,
                 secret=None,
                 base_url=None,
                 api_version=None,
                 timeout=305):

        self.secret = secret
        self.timeout = timeout

        if base_url:
            self.base_url = base_url

        if api_version:
            self.api_version = api_version

        self.session = _create_session()

    def fulfill(self, method, *args, **kwargs):
        return getattr(self.session, method)(*args, **kwargs)

    def perform(self, method, path, **kwargs):
        raw = kwargs.pop('raw', False)
        url = "{0}{1}".format(self.base_url, path)

        headers = {
            "Accept-Version": 'v%s' % self.api_version,
            "User-Agent": "quickpay-python-client, v%s" % quickpay.__version__
        }

        if self.secret:
            headers["Authorization"
                    ] = "Basic {0}".format(_base64_encode(self.secret))

        if method in ['put', 'post', 'patch']:
            headers['content-type'] = 'application/json'
            response = self.fulfill(method, url,
                                    data=json.dumps(kwargs),
                                    headers=headers,
                                    timeout=self.timeout)
        else:
            response = self.fulfill(method, url,
                                    params=kwargs,
                                    headers=headers,
                                    timeout=self.timeout)

        if response.headers.get('content-type') == 'application/json':
            body = response.json()
        else:
            body = response.text

        if response.status_code >= 400:
            raise exceptions.ApiError(body,
                                      status_code=response.status_code,
                                      url=response.url)

        if raw:
            return [response.status_code, response.text, response.headers]
        else:
            return body


def _base64_encode(string_to_encode):
    try:
        # python 2
        return base64.b64encode(string_to_encode)
    except TypeError:
        # python 3
        encoding = sys.getdefaultencoding()
        base64_bytes = base64.b64encode(bytes(string_to_encode, encoding))
        return base64_bytes.decode(encoding)


def _create_session():
    session = requests.Session()
    session.mount('https://', QPAdapter())
    return session
