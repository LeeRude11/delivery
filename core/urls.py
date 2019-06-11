from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('delivery', views.delivery, name='delivery'),
    path('info', views.info, name='info'),
    path('contacts', views.contacts, name='contacts')
]
