from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from menu.models import MenuItem


def shopping_cart(request):
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))
    template_name = 'orders/shopping_cart.html'
    cart_context = build_cart_context(request.session.get('cart', {}))
    return render(request, template_name, cart_context)


def build_cart_context(cart_dict):
    cart_cost = 0
    contents = []
    for item, amount in cart_dict.items():
        current_item = MenuItem.objects.get(pk=item)
        cost = current_item.price * int(amount)
        contents.append({
            'name': current_item.name,
            'price': current_item.price,
            'amount': int(amount),
            'cost': cost
        })
        cart_cost += cost
    return {'cart_cost': cart_cost, 'contents': contents}
