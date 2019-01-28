from django.db import models
from django.contrib.auth.models import User


class OrderInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # TODO: a function to process OrderContents and return cost
    cost = models.IntegerField(default=1)
    # TODO: a function to process OrderLog and return current status
    status = None


class OrderContents(models.Model):
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE)
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE)
    amount = models.IntegerField(default=1)


class OrderLog(models.Model):
    # TODO: plug OrderInfo
    foreign_order_id = None
    # TODO: datetime format
    ordered = None
    cooked = None
    delivered = None
