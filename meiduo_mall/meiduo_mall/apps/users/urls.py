from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^index/$', views.index),
    url(r'^regiter/$', views.regiter.as_view()),
    url(r'^login/$', views.LoginView.as_view()),
    url(r'^logout/$', views.LogOutView.as_view()),
    url(r'^info/$', views.InfoView.as_view()),
    url(r'^password/$', views.ChangePasswordView.as_view()),

]
