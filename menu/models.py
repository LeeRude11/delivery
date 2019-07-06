from django.db import models
from django.core.validators import MinValueValidator

# TODO actual img
DEFAULT_ITEM_IMG = 'menu_items/default.png'
DEFAULT_SPECIAL_IMG = 'menu_specials/default.png'


class MenuItem(models.Model):
    name = models.CharField(max_length=64, unique=True)
    price = models.IntegerField(validators=[MinValueValidator(1)])
    image = models.ImageField(
        upload_to='menu_items/',
        default=DEFAULT_ITEM_IMG)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MenuSpecial(models.Model):
    """
    Placeholder model.
    """
    name = models.CharField(max_length=64, unique=True)
    image = models.ImageField(
        upload_to='menu_specials/',
        default=DEFAULT_SPECIAL_IMG)
    available = models.BooleanField(default=True)
