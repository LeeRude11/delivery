from django.views import generic
from django.shortcuts import get_object_or_404
from django.http import (
    HttpResponseRedirect, JsonResponse, HttpResponseBadRequest)
from django.urls import reverse
from django.contrib import messages

from .models import MenuItem

UPD_ACTIONS = {
    'increase': 1,
    'decrease': -1,
    'remove': None
}


class MenuListView(generic.ListView):
    template_name = 'menu/index.html'
    model = MenuItem


class MenuItemView(generic.DetailView):
    template_name = 'menu/detail.html'
    model = MenuItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        key = str(self.kwargs['pk'])
        try:
            cur_amount = int(self.request.session['cart'][key])
        except KeyError:
            context['current_amount'] = 0
        else:
            context['current_amount'] = cur_amount
        return context


def old_update_cart(request, menuitem_id):

    menuitem = get_object_or_404(MenuItem, pk=menuitem_id)
    if request.method != 'POST':
        return HttpResponseRedirect(
            reverse('menu:detail', args=(menuitem.id,)))

    amount_to_add = request.POST.get('amount', '')
    if amount_to_add.isdigit() is False:
        messages.error(request, "Incorrect amount.")
        return HttpResponseRedirect(
            reverse('menu:detail', args=(menuitem.id,)))

    cart = request.session.setdefault('cart', {})
    key = str(menuitem_id)

    added_cost = (int(amount_to_add) - int(cart.get(key, 0))) * menuitem.price
    request.session['cart_cost'] = request.session.setdefault(
        'cart_cost', 0) + added_cost

    if int(amount_to_add) == 0:
        cart.pop(key, None)
    else:
        cart[key] = amount_to_add

    request.session.modified = True
    return HttpResponseRedirect(reverse('menu:menu'))


def update_cart(request):
    if request.method != 'GET':
        return HttpResponseRedirect(
            reverse('menu:menu'))

    item_id = request.GET.get('item_id', '')
    # TODO 404 in AJAX?
    menuitem = get_object_or_404(MenuItem, pk=item_id)

    cart = request.session.setdefault('cart', {})
    key = str(item_id)

    action = request.GET.get('action', '')
    try:
        amount_to_add = UPD_ACTIONS[action] or -int(cart[key])
    except(KeyError):
        return HttpResponseBadRequest()
    # TODO - a reasonable upper limit

    # TODO str?
    new_amount = int(cart.setdefault(key, '0')) + amount_to_add
    if new_amount < 0:
        # can't lower zero amount
        return HttpResponseBadRequest()
    elif new_amount == 0:
        cost_change = -(int(cart[key]) * menuitem.price)
        cart.pop(key)
    else:
        cost_change = amount_to_add * menuitem.price
        cart[key] = str(int(cart[key]) + amount_to_add)

    new_cost = request.session['cart_cost'] = request.session.setdefault(
        'cart_cost', 0) + cost_change

    request.session.modified = True

    return JsonResponse({'new_cost': new_cost})
