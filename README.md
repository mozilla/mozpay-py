Python module to work with Mozilla Marketplace in-app payments.

You can read all about how in-app payments work in the
[developer docs](https://developer.mozilla.org/en/Apps/In-app_payments).

Mozilla's in-app payments allow you to operate an app that accepts
payments for digital goods. As payments are completed, the Mozilla Marketplace
needs to communicate the transaction ID to your app. You can use this library to
validate the signature of that communication.

Installation
============

With [pip](http://www.pip-installer.org/) or easy_install:

    pip install moz_inapp_pay

Verify a postback
=================

    import logging
    from moz_inapp_pay import InvalidJWT, process_postback
    try:
        data = process_postback(signed_request,
                                app_key,
                                app_secret)
    except InvalidJWT:
        loggging.exception('in postback')
        return

    print data['response']['transactionID']

Verify a chargeback
===================

    import logging
    from moz_inapp_pay import InvalidJWT, process_chargeback
    try:
        data = process_chargeback(signed_request,
                                  app_key,
                                  app_secret)
    except InvalidJWT:
        logging.exception('in chargeback')
        return

    print data['response']['transactionID']
    print data['response']['reason']
