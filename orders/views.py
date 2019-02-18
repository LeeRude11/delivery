from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .models import OrderInfo, OrderContents
from menu.models import MenuItem
from menu.views import update_cart


def shopping_cart(request):
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))
    template_name = 'orders/shopping_cart.html'
    cart_contents = build_cart_contents(request.session.get('cart', {}))
    return render(request, template_name, cart_contents)


def orders_update_cart(request, menuitem_id):
    update_cart(request, menuitem_id)
    return shopping_cart(request)


def checkout(request):
    # TODO retrieve user info and fill forms
    # TODO there also will be a register option for anons
    cart = request.session.get('cart', {})
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return HttpResponseRedirect(reverse('orders:shopping_cart'))
    return render(request, 'orders/checkout.html')


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

        request.session['cart'].clear()
        request.session.modified = True

        return render(request, 'orders/success.html')

    else:
        return HttpResponseRedirect(reverse('orders:shopping_cart'))


def build_cart_contents(cart_dict):
    contents = []
    for item, amount in cart_dict.items():
        current_item = MenuItem.objects.get(pk=item)
        cost = current_item.price * int(amount)
        contents.append({
            'id': current_item.id,
            'name': current_item.name,
            'price': current_item.price,
            'amount': int(amount),
            'cost': cost
        })
    return {'contents': contents}


def write_order_to_db(user, cart):
    new_order = OrderInfo.objects.create(user=user)
    for item, amount in cart.items():
        menu_item = MenuItem.objects.get(pk=item)
        OrderContents.objects.create(
            order=new_order, menu_item=menu_item, amount=int(amount))
