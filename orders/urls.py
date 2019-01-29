from django.urls import path

from . import views

app_name = 'orders'
urlpatterns = [
    path('shopping_cart/', views.ShoppingCartView.as_view(),
         name='shopping_cart')
]
