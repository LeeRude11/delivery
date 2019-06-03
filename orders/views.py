from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .models import OrderInfo, OrderContents
from menu.models import MenuItem
from accounts.forms import CustomOrderForm


def shopping_cart(request):
    template_name = 'orders/shopping_cart.html'
    cart_contents = build_cart_contents(request.session.get('cart', {}))
    return render(request, template_name, cart_contents)


def checkout(request):
    # TODO there also will be a register option for anons
    cart = request.session.get('cart', {})
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return HttpResponseRedirect(reverse('orders:shopping_cart'))

    if request.user.is_authenticated:
        instance = request.user
    else:
        instance = None

    if request.method == 'POST':
        form = CustomOrderForm(request.POST, instance=instance)

        if form.is_valid():
            user = form.save()
            if request.user.is_anonymous:
                # don't register a guest user
                user.set_unusable_password()
                user.is_guest = True
                user.save()

            write_order_to_db(user, cart)
            flush_cart(request.session)
            return render(request, 'orders/success.html')
    else:
        form = CustomOrderForm(instance=instance)

    return render(request, 'orders/checkout.html', {'form': form})


def flush_cart(session):
    session['cart'].clear()
    session['cart_cost'] = 0
    session.modified = True


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
