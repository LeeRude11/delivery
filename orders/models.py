from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

MAX_ORDER_VOLUME = 20


class OrderInfo(models.Model):
    """
    Top order object bound to user with cost and status functions
    calculated with belonging OrderContents and OrderLog classes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def cost(self):
        cost = 0
        for order_item in self.ordercontents_set.all():
            cost += order_item.amount * order_item.menu_item.price
        return cost

    # TODO: a function to process OrderLog and return current status
    status = None


class OrderContents(models.Model):
    """
    A single MenuItem, its amount and corresponding order.
    """
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE)
    amount = models.IntegerField(
        default=1,
        validators=[MaxValueValidator(MAX_ORDER_VOLUME), MinValueValidator(1)])


class OrderLog(models.Model):
    """
    A single order state change timings to be gradually filled.
    """
    # TODO: plug OrderInfo
    foreign_order_id = None
    # TODO: datetime format
    ordered = None
    cooked = None
    delivered = None
