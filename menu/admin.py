from django.contrib import admin

from .models import MenuItem


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('available', '__str__', 'price')

    actions = ['make_available', 'make_unavailable']

    def make_available(self, request, queryset):
        self._change_availability(
            request, queryset, True, "%s successfully made available.")

    make_available.short_description = (
        "Make selected items available to customers")

    def make_unavailable(self, request, queryset):
        self._change_availability(
            request, queryset, False, "%s successfully hidden.")

    make_unavailable.short_description = "Hide selected items from customers"

    def _change_availability(self, request, queryset, available, message):
        rows_updated = queryset.update(available=available)
        if rows_updated == 1:
            message_bit = "1 item was"
        else:
            message_bit = "%s items were" % rows_updated
        self.message_user(
            request, message % message_bit)


admin.site.register(MenuItem, MenuItemAdmin)
