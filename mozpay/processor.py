from .exc import InvalidJWT
from .verify import verify_jwt

__all__ = ['process_postback', 'process_chargeback']


def process_postback(signed_postback, key, secret, **kw):
    return verify_jwt(signed_postback, key, secret, **kw)


def process_chargeback(signed_chargeback, key, secret, **kw):
    kw.setdefault('validators', [_validate_chargeback])
    return verify_jwt(signed_chargeback, key, secret, **kw)


def _validate_chargeback(jwt_data):
    if jwt_data['response'].get('reason') is None:
        raise InvalidJWT('Chargeback response did not include a reason',
                         issuer=jwt_data['iss'])
