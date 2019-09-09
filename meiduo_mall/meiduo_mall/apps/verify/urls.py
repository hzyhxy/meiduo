from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^usernames/(?P<username>\w+)/count/$', views.UserName.as_view()),
    url(r'^mobiles/(?P<mobile>\w+)/count/$', views.Mobile.as_view()),
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCode.as_view()),
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SmsCode.as_view()),
    url(r'emails/verification/', views.EmailsVerify.as_view())
]
