from django.views import generic
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from .models import MenuItem


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


def update_cart(request, menuitem_id):
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))

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
