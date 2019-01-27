from django.db import models


class OrderInfo(models.Model):
    # TODO: users from accounts app
    foreign_user_id = None
    # TODO: a function to process OrderContents and return cost
    cost = models.IntegerField
    # TODO: a function to process OrderLog and return current status
    status = None


class OrderContents(models.Model):
    # TODO: plug OrderInfo
    foreign_order_id = None
    # TODO: menu items from menu app
    foreign_menu_item_id = None
    amount = models.IntegerField


class OrderLog(models.Model):
    # TODO: plug OrderInfo
    foreign_order_id = None
    # TODO: datetime format
    ordered = None
    cooked = None
    delivered = None
