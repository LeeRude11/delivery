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


def add_to_cart(request, menuitem_id):
    menuitem = get_object_or_404(MenuItem, pk=menuitem_id)
    if request.user.is_authenticated is False:
        messages.error(request, "Must be logged in.")
        return HttpResponseRedirect(reverse('accounts:login'))

    amount_to_add = request.POST.get('amount', '')
    if amount_to_add.isdigit() is False or int(amount_to_add) == 0:
        messages.error(request, "Incorrect amount.")
        return HttpResponseRedirect(
            reverse('menu:detail', args=(menuitem.id,)))

    cart = request.session.setdefault('cart', {})
    cart[f'{menuitem_id}'] = amount_to_add

    request.session.modified = True
    return HttpResponseRedirect(reverse('menu:menu'))
