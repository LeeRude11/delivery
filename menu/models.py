from django.db import models
from django.core.validators import MinValueValidator


class MenuItem(models.Model):
    name = models.CharField(max_length=64, unique=True)
    price = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return self.name
