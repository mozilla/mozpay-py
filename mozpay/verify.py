"""
Helper functions to verify `JWT`_ (JSON Web Token) objects.
Some are specific to Firefox Marketplace payments, others are more generic.

.. _`JWT`: http://openid.net/specs/draft-jones-json-web-token-07.html
"""
import json
import sys

import jwt

from .exc import InvalidJWT, RequestExpired


def verify_jwt(signed_request, expected_aud, secret, validators=[],
               required_keys=('request.pricePoint',
                              'request.name',
                              'request.description',
                              'response.transactionID'),
               algorithms=None):
    """
    Verifies a postback/chargeback JWT.

    Returns the trusted JSON data from the original request.
    When there's an error, an exception derived from
    :class:`mozpay.exc.InvalidJWT`
    will be raised.

    This is an all-in-one function that does all verification you'd
    need. There are some low-level functions you can use to just
    verify certain parts of a JWT.

    Arguments:

    **signed_request**
        JWT byte string.

    **expected_aud**
        The expected value for the aud (audience) of the JWT.
        See :func:`mozpay.verify.verify_audience`.

    **secret**
        A shared secret to validate the JWT with.
        See :func:`mozpay.verify.verify_sig`.

    **validators**
        A list of extra callables. Each one is passed a JSON Python dict
        representing the JWT after it has passed all other checks.

    **required_keys**
        A list of JWT keys to validate. See
        :func:`mozpay.verify.verify_keys`.

    **algorithms**
        A list of valid JWT algorithms to accept.
        By default this will only include HS256 because that's
        what the Firefox Marketplace uses.
    """
    if not algorithms:
        algorithms = ['HS256']
    issuer = _get_issuer(signed_request=signed_request)
    app_req = verify_sig(signed_request, secret, issuer=issuer,
                         algorithms=algorithms, expected_aud=expected_aud)

    # I think this call can be removed after
    # https://github.com/jpadilla/pyjwt/issues/121
    verify_claims(app_req, issuer=issuer)

    verify_keys(app_req, required_keys, issuer=issuer)

    for vl in validators:
        vl(app_req)

    return app_req


def verify_claims(app_req, issuer=None):
    """
    Verify JWT claims.

    All times must be UTC unix timestamps.

    These claims will be verified:

    - iat: issued at time. If JWT was issued more than an hour ago it is
      rejected.
    - exp: expiration time.

    All exceptions are derived from
    :class:`mozpay.exc.InvalidJWT`.
    For expirations a
    :class:`mozpay.exc.RequestExpired`
    exception will be raised.
    """
    if not issuer:
        issuer = _get_issuer(app_req=app_req)
    try:
        float(str(app_req.get('exp')))
        float(str(app_req.get('iat')))
    except ValueError:
        _re_raise_as(InvalidJWT,
                     'JWT had an invalid exp (%r) or iat (%r) '
                     % (app_req.get('exp'), app_req.get('iat')),
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
                "pricePoint": 1,
            }
        }

    You could verify the presence of all keys and retrieve
    their values like this::

        iss, aud, price = verify_keys(jwt_dict,
                                      ('iss',
                                       'aud',
                                       'request.pricePoint'))

    Do you see how the comma separated assigned variables
    match the keys that were extracted? The order is important.

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


def verify_sig(signed_request, secret, issuer=None, algorithms=None,
               expected_aud=None):
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
        jwt.decode(signed_request, secret, verify=True,
                   algorithms=algorithms, audience=expected_aud)
    except jwt.ExpiredSignatureError, exc:
        _re_raise_as(RequestExpired, '%s' % exc, issuer=issuer)
    except jwt.InvalidTokenError, exc:
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
