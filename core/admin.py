from django.contrib import admin

from .models import InfoViewTemplate


class InfoViewTemplateAdmin(admin.ModelAdmin):
    pass


admin.site.register(InfoViewTemplate)
