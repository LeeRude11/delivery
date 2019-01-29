from django.views import generic

from .models import OrderInfo


class ShoppingCartView(generic.ListView):
    template_name = 'orders/shopping_cart.html'
    model = OrderInfo
