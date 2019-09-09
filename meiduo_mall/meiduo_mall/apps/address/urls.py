from django.conf.urls import url, include
from . import views
urlpatterns = [
    url(r'^addresses/$', views.AddressesView.as_view()),
    url(r'^addresses/(\d+)/$', views.AddressesView.as_view()),
    url(r'^areas/$', views.AreasView.as_view()),
    url(r'addresses/create', views.CreateAddressView.as_view()),
    url(r'addresses/(\d+)/default', views.DefaultAdressesView.as_view()),
    url(r'addresses/(\d+)/title/', views.UpdateTitleAddressView.as_view()),
]
