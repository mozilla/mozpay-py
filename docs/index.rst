=============
mozpay
=============

A Python module to make web payments with Mozilla's
`navigator.mozPay()`_.

You can read all about how web payments work in the
`developer docs`_.

Mozilla's web payments allow you to operate an app (or website) that accepts
payments for digital goods. As payments are completed, the Firefox Marketplace
needs to communicate the transaction ID to your app. You can use this library to
validate the signature of that communication.
All communication is done via signed `JWT`_ (JSON Web Token).

This also includes some generic ways to validate `JWT`_ objects.
Hmm, maybe that should be extracted for more general use.

.. contents::
    :local:

.. _`navigator.mozPay()`: https://wiki.mozilla.org/WebAPI/WebPayment
.. _`developer docs`: https://developer.mozilla.org/en-US/docs/Apps/Publishing/In-app_payments
.. _`JWT`: http://openid.net/specs/draft-jones-json-web-token-07.html


Installation
============

With `pip`_ or easy_install, run::

    pip install mozpay

Or install it from source::

    pip install git+git://github.com/mozilla/mozpay-py.git

.. _`pip`: http://www.pip-installer.org/

Verify a postback
=================

.. highlight:: python

::

    import logging
    from mozpay import InvalidJWT, process_postback
    try:
        data = process_postback(signed_request,
                                app_key,
                                app_secret)
        print data['response']['transactionID']
    except InvalidJWT:
        loggging.exception('in postback')


Verify a chargeback
===================

::

    import logging
    from mozpay import InvalidJWT, process_chargeback
    try:
        data = process_chargeback(signed_request,
                                  app_key,
                                  app_secret)
        print data['response']['transactionID']
        print data['response']['reason']
    except InvalidJWT:
        logging.exception('in chargeback')


Use It With Django
==================

If you use the `Django`_ framework,
there's an app you can plug right into your urls.py.

.. _Django: https://www.djangoproject.com/

Add the app in your settings.py file::

    INSTALLED_APPS = [
        # ...
        'mozpay.djangoapp',
    ]

Add your key and secret that was granted by the Firefox Marketplace to your
**local** settings.py file::

    MOZ_APP_KEY = '<from marketplace.mozilla.org>'
    MOZ_APP_SECRET = '<from marketplace.mozilla.org>'

.. note::

    Do not commit your secret to a public repo. **Always keep it secure on your
    server**. Never expose it to the client in JavaScript or anywhere else.

Add the postback / chargeback URLs to your urls.py file::

    from django.conf.urls.defaults import patterns, include

    urlpatterns = patterns('',
        ('^moz/', include('mozpay.djangoapp.urls')),
    )

This will add ``/moz/postback`` and ``/moz/chargeback`` to your URLs.
You'll enter these callback URLs into the in-app payment config screen on the
Firefox Marketplace.

If you want to do further processing on the postbacks, you can connect to a
few signals. Here is an example of code to go in your app
(probably in models.py)::

    import logging
    from django.dispatch import receiver

    from mozpay.djangoapp.signals import (moz_inapp_postback,
                                          moz_inapp_chargeback)


    @receiver(moz_inapp_postback)
    def mozmarket_postback(request, jwt_data, **kwargs):
        logging.info('transaction ID %s processed ok'
                     % jwt_data['response']['transactionID'])


    @receiver(moz_inapp_chargeback)
    def mozmarket_chargeback(request, jwt_data, **kwargs):
        logging.info('transaction ID %s charged back; reason: %r'
                     % (jwt_data['response']['transactionID'],
                        jwt_data['response']['reason']))


Exceptions are logged to the channel ``mozpay.djangoapp.views``
so be sure to add the appropriate handlers to that.

When an InvalidJWT exception occurs, a 400 Bad Request is returned.

JWT Verification API
====================

.. automodule:: mozpay.verify
    :members: verify_jwt, verify_sig, verify_claims, verify_keys

Exceptions
==========

.. automodule:: mozpay.exc
    :members:

Source Code and Bug Tracker
===========================

The source code is hosted on https://github.com/mozilla/mozpay-py
and you can submit pull requests and bugs over there.

Developers
==========

Hello!
To work on this module, check out the source from git and be sure
you have the tox_ tool. To run the test suite, cd into the root and type::

    tox

This will run all tests in a virtualenv using the supported versions of Python.

To build the documentation, create a virtualenv then run::

    pip install -r docs/requirements.txt

Build the docs from the root like this::

    make -C docs/ html

Et voila::

    open docs/_build/html/index.html

.. _tox: http://tox.testrun.org/latest/

Changelog
=========

* 2.1.0

  * Added ``algorithms`` list to verification functions to adjust
    what JWT algorithms are accepted.
    **By default only HS256 is accepted now**.
  * Upgraded `PyJWT <https://github.com/jpadilla/pyjwt>`_ to the latest version.
  * Removed M2Crypto as a dependency because that is no longer needed
    and it wasn't actually used for our signing purposes anyway.

* 2.0.0

  * Changed postback/chargeback from reading a JWT in the post body to reading
    it from the ``notice`` parameter.
    See https://bugzilla.mozilla.org/show_bug.cgi?id=838066 for details.

* 1.0.4

  * First working release.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

