from django.conf.urls import url, include
from . import views
urlpatterns = [
    url(r'^image/$', views.ImageView.as_view()),
    url(r'^index/$', views.IndexView.as_view()),
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),

]
