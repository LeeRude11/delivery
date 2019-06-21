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

    def get_queryset(self):
        return MenuItem.objects.exclude(available=False)


class MenuItemView(generic.DetailView):
    template_name = 'menu/detail.html'
    model = MenuItem

    def get_object(self):
        pk = self.kwargs['pk']
        return get_object_or_404(MenuItem, pk=pk, available=True)


def specials(request):
    # TODO
    """
    Information about current specials.
    """
    template_name = 'menu/specials.html'
    return render(request, template_name)


def cart_debug(request):
    """
    """
    if not request.user.is_admin:
        return HttpResponseRedirect(
            reverse('menu:menu'))
    print(request.session['cart'])
    print(request.session['cart_cost'])

    del request.session['cart']
    request.session['cart_cost'] = 0

    return HttpResponseRedirect(
        reverse('menu:menu'))


def update_cart(request):
    if request.method != 'GET':
        return HttpResponseRedirect(
            reverse('menu:menu'))

    # TODO '' goes through and raises exception, so 'or None' is needed
    item_id = request.GET.get('item_id') or None
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
