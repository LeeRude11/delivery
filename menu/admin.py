from django.contrib import admin

from .models import MenuItem


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('available', '__str__', 'price')

    actions = ['make_available', 'make_unavailable']

    def make_available(self, request, queryset):
        rows_updated = queryset.update(available=True)
        if rows_updated == 1:
            message_bit = "1 item was"
        else:
            message_bit = "%s items were" % rows_updated
        self.message_user(
            request, "%s successfully made available." % message_bit)

    make_available.short_description = (
        "Make selected items available to customers")

    def make_unavailable(self, request, queryset):
        rows_updated = queryset.update(available=False)
        if rows_updated == 1:
            message_bit = "1 item was"
        else:
            message_bit = "%s items were" % rows_updated
        self.message_user(
            request, "%s successfully hidden." % message_bit)

    make_unavailable.short_description = "Hide selected items from customers"


admin.site.register(MenuItem, MenuItemAdmin)
