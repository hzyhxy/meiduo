from django.conf.urls import url, include
from . import views
urlpatterns = [
    url(r'^image/$', views.ImageView.as_view()),
    url(r'^index/$', views.IndexView.as_view()),
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view()),
    url(r'^detail/visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view()),
    url(r'^browse_histories/$', views.HistoriesView.as_view()),

]
