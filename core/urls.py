from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.index, name='index'),
    path('delivery', views.delivery, name='delivery'),
    path('info', views.info, name='info'),
    path('contacts', views.contacts, name='contacts'),
    # TODO development serving
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
