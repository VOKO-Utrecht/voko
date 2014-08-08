from .models import OrderRound, Order, OrderProduct


def get_current_order_round():
    ## TODO: Get current order round based on current date
    ## If non existing, get_or_create?
    try:
        return list(OrderRound.objects.all())[-1]
    except IndexError:
        return


def get_or_create_order(user):
    return Order.objects.get_or_create(finalized=False,
                                       defaults={'order_round': OrderRound.objects.order_by('-pk')[0],
                                                 'user': user})[0]


def get_order_product(product, order):
    existing_ops = OrderProduct.objects.filter(product=product, order=order)
    if existing_ops:
        return existing_ops[0]