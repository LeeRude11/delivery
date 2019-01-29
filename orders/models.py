from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

MAX_ORDER_VOLUME = 20


class OrderInfo(models.Model):
    """
    Order object bound to user with cost function
    calculated with belonging OrderContents.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_cost(self):
        """
        Calculate cost with bound OrderContents objects.
        """
        cost = 0
        for order_item in self.ordercontents_set.all():
            cost += order_item.amount * order_item.menu_item.price
        return cost

    # State properties
    ordered = models.DateTimeField(
        'date order was placed', auto_now_add=True)
    cooked = models.DateTimeField(
        'date order was cooked', null=True, blank=True)
    delivered = models.DateTimeField(
        'date order was delivered', null=True, blank=True)

    def update_current_state(self):
        """
        When called, timing properties are gradually updated.
        """
        if self.cooked is None:
            self.cooked = timezone.now()
        else:
            self.delivered = timezone.now()


class OrderContents(models.Model):
    """
    A single MenuItem, its amount and corresponding order.
    """
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE)
    amount = models.IntegerField(
        default=1,
        validators=[MaxValueValidator(MAX_ORDER_VOLUME), MinValueValidator(1)])
