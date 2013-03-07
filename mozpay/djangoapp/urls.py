from django.conf.urls.defaults import *

from . import views


urlpatterns = patterns('',
    url(r'^postback$', views.postback,
        name='mozpay.postback'),
    url(r'^chargeback$', views.chargeback,
        name='mozpay.chargeback'),
)
