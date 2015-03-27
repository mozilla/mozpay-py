import calendar
from datetime import datetime, timedelta
import time

from nose.tools import raises

import mozpay
from mozpay.exc import InvalidJWT, RequestExpired

from . import JWTtester


class TestVerify(JWTtester):

    def setUp(self):
        super(TestVerify, self).setUp()
        self.verifier = mozpay.process_postback

    @raises(InvalidJWT)
    def test_unknown_secret(self):
        self.verify(self.request(app_secret='invalid'))

    @raises(InvalidJWT)
    def test_garbage_request(self):
        self.verify('<not valid JWT>')

    @raises(InvalidJWT)
    def test_non_ascii_jwt(self):
        self.verify(u'Ivan Krsti\u0107 is in your JWT')

    @raises(RequestExpired)
    def test_expired(self):
        now = calendar.timegm(time.gmtime())
        old = datetime.utcfromtimestamp(now) - timedelta(minutes=1)
        exp = calendar.timegm(old.timetuple())
        self.verify(self.request(exp=exp))

    @raises(RequestExpired)
    def test_expired_iat(self):
        old = calendar.timegm(time.gmtime()) - 3660  # 1hr, 1min ago
        self.verify(self.request(iat=old))

    @raises(InvalidJWT)
    def test_invalid_expiry(self):
        self.verify(self.request(exp='<not a number>'))

    @raises(InvalidJWT)
    def test_invalid_expiry_non_ascii(self):
        self.verify(update={'exp': u'Ivan Krsti\u0107 is in your JWT'})

    @raises(RequestExpired)
    def test_none_expiry(self):
        self.verify(update={'exp': None})

    @raises(InvalidJWT)
    def test_invalid_iat_non_ascii(self):
        self.verify(update={'iat': u'Ivan Krsti\u0107 is in your JWT'})

    @raises(InvalidJWT)
    def test_not_before(self):
        nbf = calendar.timegm(time.gmtime()) + 310  # 5:10 in the future
        self.verify(update={'nbf': nbf})

    @raises(InvalidJWT)
    def test_require_iss(self):
        payload = self.payload()
        del payload['iss']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_price_point(self):
        payload = self.payload()
        del payload['request']['pricePoint']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_name(self):
        payload = self.payload()
        del payload['request']['name']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_description(self):
        payload = self.payload()
        del payload['request']['description']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_request(self):
        payload = self.payload()
        del payload['request']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_response(self):
        payload = self.payload()
        del payload['response']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_require_transaction_id(self):
        payload = self.payload()
        del payload['response']['transactionID']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_invalid_audience(self):
        self.verify(update={'aud': 'not my app'})

    @raises(InvalidJWT)
    def test_missing_audience(self):
        payload = self.payload()
        del payload['aud']
        self.verify(self.request(payload=payload))

    @raises(InvalidJWT)
    def test_malformed_jwt(self):
        self.verify(self.request() + 'x')

    @raises(InvalidJWT)
    def test_unsupported_algorithm(self):
        # Configure mozpay to only accept the HS384 algorithm.
        self.verify(self.request(encode_kwargs={'algorithm': 'HS256'}),
                    verify_kwargs={'algorithms': ['HS384']})

    @raises(InvalidJWT)
    def test_hs256_is_default_algorithm(self):
        # By default, only HS256 JWTs are accepted.
        self.verify(self.request(encode_kwargs={'algorithm': 'HS384'}))
