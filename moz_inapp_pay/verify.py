"""
Helper functions to verify `JWT`_ (JSON Web Token) objects.
Some are specific to Mozilla Marketplace payments, others are more generic.

.. _`JWT`: http://openid.net/specs/draft-jones-json-web-token-07.html
"""
import calendar
from datetime import datetime
import json
import sys
import time

import jwt

from .exc import InvalidJWT, RequestExpired


def verify_jwt(signed_request, key, secret, validators=[],
               required_keys=('request.price',
                              'request.currency',
                              'request.name',
                              'request.description',
                              'response.transactionID')):
    """
    Verifies a postback/chargeback JWT.

    Returns the trusted JSON data from the original request.
    When there's an error, an exception derived from
    :class:`moz_inapp_pay.exc.InvalidJWT`
    will be raised.

    This is an all-in-one function that does all verification you'd
    need. There are some low-level functions you can use to just
    verify certain parts of a JWT.
    """
    issuer = _get_issuer(signed_request=signed_request)
    app_req = verify_sig(signed_request, secret, issuer=issuer)
    verify_claims(app_req, issuer=issuer)
    verify_audience(app_req, key, issuer=issuer)
    verify_keys(app_req, required_keys, issuer=issuer)

    for vl in validators:
        vl(app_req)

    return app_req


def verify_audience(app_req, expected_aud, issuer=None):
    """
    Verify JWT aud (audience)

    When aud is not found or doesn't match expected_aud,
    :class:`moz_inapp_pay.exc.InvalidJWT`
    is raised.

    The valid audience is returned
    """
    if not issuer:
        issuer = _get_issuer(app_req=app_req)

    audience, = verify_keys(app_req, ['aud'])
    if audience != expected_aud:
        raise InvalidJWT('JWT aud (audience) must be set to %r; '
                         'got: %r' % (expected_aud, audience),
                         issuer=issuer)
    return audience


def verify_claims(app_req, issuer=None):
    """
    Verify JWT claims.

    All times must be UTC unix timestamps.

    These claims will be verified:

    - iat: issued at time. If JWT was issued more than an hour ago it is
      rejected.
    - exp: expiration time.
    - nbf: not before time. This is padded with 5 minutes for clock skew.
      This field is *optional*, leaving it out is not an error.

    All exceptions are derived from
    :class:`moz_inapp_pay.exc.InvalidJWT`.
    For expirations a
    :class:`moz_inapp_pay.exc.RequestExpired`
    exception will be raised.
    """
    if not issuer:
        issuer = _get_issuer(app_req=app_req)
    try:
        expires = float(str(app_req.get('exp')))
        issued = float(str(app_req.get('iat')))
    except ValueError:
        _re_raise_as(InvalidJWT,
                     'JWT had an invalid exp (%r) or iat (%r) '
                     % (app_req.get('exp'), app_req.get('iat')),
                     issuer=issuer)
    now = calendar.timegm(time.gmtime())
    if expires < now:
        raise RequestExpired('JWT expired: %s UTC < %s UTC '
                             '(issued at %s UTC)'
                             % (datetime.utcfromtimestamp(expires),
                                datetime.utcfromtimestamp(now),
                                datetime.utcfromtimestamp(issued)),
                             issuer=issuer)
    if issued < (now - 3600):  # issued more than an hour ago
        raise RequestExpired('JWT iat expired: %s UTC < %s UTC '
                             % (datetime.utcfromtimestamp(issued),
                                datetime.utcfromtimestamp(now)),
                             issuer=issuer)
    try:
        not_before = float(str(app_req.get('nbf')))
    except ValueError:
        app_req['nbf'] = None  # this field is optional
    else:
        about_now = now + 300  # pad 5 minutes for clock skew
        if not_before >= about_now:
            raise InvalidJWT('JWT cannot be processed before '
                             '%s UTC (nbf must be < %s UTC)'
                             % (datetime.utcfromtimestamp(not_before),
                                datetime.utcfromtimestamp(about_now)),
                             issuer=issuer)


def verify_keys(app_req, required_keys, issuer=None):
    """
    Verify all JWT object keys listed in required_keys.

    Each required key is specified as a dot-separated path.
    The key values are returned as a list ordered by how
    you specified them.

    Take this JWT for example::

        {
            "iss": "...",
            "aud": "...",
            "request": {
                "price": "0.99",
                "currency": "USD"
            }
        }

    You could verify the presence of all keys and retrieve
    their values like this::

        iss, aud, price, curr = verify_keys(jwt_dict,
                                            ('iss',
                                             'aud',
                                             'request.price',
                                             'request.currency'))

    """
    if not issuer:
        issuer = _get_issuer(app_req=app_req)
    key_vals = []
    for key_path in required_keys:
        parent = app_req
        for kp in key_path.split('.'):
            if not isinstance(parent, dict):
                raise InvalidJWT('JWT is missing %r: %s is not a dict'
                                 % (key_path, kp), issuer=issuer)
            val = parent.get(kp, None)
            if not val:
                raise InvalidJWT('JWT is missing %r: %s is not a valid key'
                                 % (key_path, kp), issuer=issuer)
            parent = val
        key_vals.append(parent)  # last value of key_path
    return key_vals


def verify_sig(signed_request, secret, issuer=None):
    """
    Verify the JWT signature.

    Given a raw JWT, this verifies it was signed with
    *secret*, decodes it, and returns the JSON dict.
    """
    if not issuer:
        issuer = _get_issuer(signed_request=signed_request)
    signed_request = _to_bytes(signed_request)
    app_req = _get_json(signed_request)

    # Check signature.
    try:
        jwt.decode(signed_request, secret, verify=True)
    except jwt.DecodeError, exc:
        _re_raise_as(InvalidJWT,
                     'Signature verification failed: %s' % exc,
                     issuer=issuer)
    return app_req


def _get_json(signed_request):
    signed_request = _to_bytes(signed_request)
    try:
        app_req = jwt.decode(signed_request, verify=False)
    except jwt.DecodeError, exc:
        _re_raise_as(InvalidJWT, 'Invalid JWT: %s' % exc)
    if not isinstance(app_req, dict):
        try:
            app_req = json.loads(app_req)
        except ValueError, exc:
            _re_raise_as(InvalidJWT,
                         'Invalid JSON for JWT: %s' % exc)
    return app_req


def _get_issuer(signed_request=None, app_req=None):
    if not app_req:
        if not signed_request:
            raise TypeError('need either signed_request or app_req')
        app_req = _get_json(signed_request)

    # Check JWT issuer.
    issuer = app_req.get('iss', None)
    if not issuer:
        raise InvalidJWT('Payment JWT is missing iss (issuer)')
    return issuer


def _to_bytes(signed_request):
    try:
        return str(signed_request)  # must be base64 encoded bytes
    except UnicodeEncodeError, exc:
        _re_raise_as(InvalidJWT,
                     'Non-ascii payment JWT: %s' % exc)


def _re_raise_as(NewExc, *args, **kw):
    """Raise a new exception using the preserved traceback of the last one."""
    etype, val, tb = sys.exc_info()
    raise NewExc(*args, **kw), None, tb
