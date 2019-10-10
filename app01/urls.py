from django.conf.urls import url
from django.contrib import admin
from app01 import views

urlpatterns = [
    url(r'^$', views.hello),
    url(r'^ks_order$', views.ks_order),
    url(r'^login$', views.login),
    url(r'^check-login$', views.check_login),
    url(r'^user$', views.user),
    url(r'^contact_list$', views.contact_list),
    url(r'^send_msg$', views.send_msg),
    url(r'^get_msg$', views.get_msg),
]
