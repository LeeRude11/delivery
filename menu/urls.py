from django.urls import path

from . import views

app_name = 'menu'
urlpatterns = [
    path('', views.MenuListView.as_view(), name='menu'),
    path('<int:pk>/', views.MenuItemView.as_view(), name='detail'),
    path('<int:menuitem_id>/update_cart',
         views.update_cart, name='update_cart')
]
