from django.urls import path

from . import views

app_name = 'menu'
urlpatterns = [
    path('', views.MenuListView.as_view(), name='menu'),
    path('<int:pk>/', views.MenuItemView.as_view(), name='detail'),
    path('<int:menuitem_id>/add_to_cart',
         views.add_to_cart, name='add_to_cart')
]
