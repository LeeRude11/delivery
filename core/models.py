from django.db import models

from string import capwords

TEMPLATES_FOLDER = 'core/info_sub/'
DEFAULT_TEMPLATE = 'default_info'


class InfoViewTemplate(models.Model):
    view_name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=64, unique=True, blank=True)
    template_name = models.CharField(max_length=64, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if self.title == '':
            self.title = capwords(self.view_name)
        if self.template_name == '':
            self.template_name = DEFAULT_TEMPLATE
        self.template_name = f'{TEMPLATES_FOLDER}{self.template_name}.html'
        super().save(*args, **kwargs)
