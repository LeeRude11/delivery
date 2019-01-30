from django.contrib import admin

from .models import OrderInfo, OrderContents


class OrderContentsInline(admin.TabularInline):
    model = OrderContents
    extra = 0


class OrderInfoAdmin(admin.ModelAdmin):
    inlines = [OrderContentsInline]
    list_display = ('id', 'ordered', 'cooked', 'delivered', 'cost')


admin.site.register(OrderInfo, OrderInfoAdmin)
