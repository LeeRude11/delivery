from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .models import OrderInfo, OrderContents
from menu.models import MenuItem


def shopping_cart(request):
    # TODO remove and modify items; grey out 'zeroed' items
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))
    template_name = 'orders/shopping_cart.html'
    cart_context = build_cart_context(request.session.get('cart', {}))
    return render(request, template_name, cart_context)


def process_order(request):
    # TODO receive more info in POST
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))

    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if len(cart) == 0:
            messages.error(request, "Your cart is empty.")
            return HttpResponseRedirect(reverse('orders:shopping_cart'))
        write_order_to_db(request.user, cart)
        return render(request, 'orders/success.html')

    else:
        return HttpResponseRedirect(reverse('orders:shopping_cart'))


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


def write_order_to_db(user, cart):
    new_order = OrderInfo.objects.create(user=user)
    for item, amount in cart.items():
        menu_item = MenuItem.objects.get(pk=item)
        OrderContents.objects.create(
            order=new_order, menu_item=menu_item, amount=int(amount))
