from django.contrib import admin
from django.utils.translation import ugettext as _

from .models import OrderInfo, OrderContents


class OrderContentsInline(admin.TabularInline):
    model = OrderContents
    extra = 0


class DeliveredListFilter(admin.SimpleListFilter):

    title = _('Is delivered')

    parameter_name = 'is delivered'

    def lookups(self, request, model_admin):

        return (
            ('yes', _('Yes')),
            ('no',  _('No')),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(delivered__isnull=False)

        if self.value() == 'no':
            return queryset.filter(delivered__isnull=True)


class OrderInfoAdmin(admin.ModelAdmin):
    inlines = [OrderContentsInline]
    list_display = ('id', 'ordered', 'cooked', 'delivered', 'total_cost')
    list_filter = [DeliveredListFilter]


admin.site.register(OrderInfo, OrderInfoAdmin)
