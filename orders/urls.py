from django.urls import path

from . import views

app_name = 'orders'
urlpatterns = [
    path('shopping_cart/', views.shopping_cart, name='shopping_cart'),
    path('<int:menuitem_id>/update_cart', views.orders_update_cart,
         name='orders_update_cart'),
    path('<int:menuitem_id>/remove_item', views.remove_item,
         name='remove_item'),
    path('checkout/', views.checkout, name='checkout'),
]
