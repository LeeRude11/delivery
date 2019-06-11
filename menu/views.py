from django.views import generic
from django.shortcuts import get_object_or_404
from django.http import (
    HttpResponseRedirect, JsonResponse, HttpResponseBadRequest)
from django.urls import reverse
from django.shortcuts import render

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
            cur_amount = self.request.session['cart'][key]
        except KeyError:
            context['current_amount'] = 0
        else:
            context['current_amount'] = cur_amount
        return context


def specials(request):
    # TODO
    """
    Information about current specials.
    """
    template_name = 'menu/specials.html'
    return render(request, template_name)


def update_cart(request):
    if request.method != 'GET':
        return HttpResponseRedirect(
            reverse('menu:menu'))

    item_id = request.GET.get('item_id', '')
    menuitem = get_object_or_404(MenuItem, pk=item_id)

    cart = request.session.setdefault('cart', {})
    key = item_id

    action = request.GET.get('action', '')
    try:
        amount_to_add = UPD_ACTIONS[action] or -cart[key]
    except(KeyError):
        return HttpResponseBadRequest()
    # TODO - a reasonable upper limit

    new_amount = cart.setdefault(key, 0) + amount_to_add
    if new_amount < 0:
        # can't lower zero amount
        return HttpResponseBadRequest()
    elif new_amount == 0:
        cost_change = -(cart[key] * menuitem.price)
        cart.pop(key)
    else:
        cost_change = amount_to_add * menuitem.price
        cart[key] = cart[key] + amount_to_add

    new_cost = request.session['cart_cost'] = request.session.setdefault(
        'cart_cost', 0) + cost_change

    request.session.modified = True

    return JsonResponse({'new_cost': new_cost})
