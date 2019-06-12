from django.template.defaulttags import register


@register.filter
def get_cart_item(session, key):
    try:
        amount = session['cart'][str(key)]
    except(KeyError):
        amount = 0
    return amount
