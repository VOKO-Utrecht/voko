from django.db import OperationalError
import models


def get_current_order_round():
    ## TODO: Get current order round based on current date
    ## If non existing, get_or_create?
    try:
        return models.OrderRound.objects.all().order_by("-pk")[0]
    except IndexError:
        print "INDEX FAIL"
        return
    except OperationalError:
        print "OPERATIONAL ERROR"
        pass


def get_or_create_order(user):
    try:
        return models.Order.objects.get_or_create(finalized=False,
                                                  user=user,
                                                  order_round=get_current_order_round(),
                                                  defaults={'order_round': models.OrderRound.objects.order_by('-pk')[0],
                                                            'user': user})[0]
    except IndexError:
        raise RuntimeError("Nog geen bestelronde aangemaakt!")


def get_order_product(product, order):
    existing_ops = models.OrderProduct.objects.filter(product=product, order=order)
    if existing_ops:
        return existing_ops[0]


def get_credit(user):
    credit = sum([b.amount for b in user.balance.filter(type="CR")])
    debit = sum([b.amount for b in user.balance.filter(type="DR")])

    return credit - debit


def get_debit(user):
    return -get_credit(user)


def update_totals_for_products_with_max_order_amounts(order):
    ### TODO: Add messages about deleted / changed orderproducts
    for orderproduct in order.orderproducts.all().exclude(product__maximum_total_order__exact=None):
        if orderproduct.amount > orderproduct.product.amount_available:
            if orderproduct.product.amount_available > 0:
                orderproduct.amount = orderproduct.product.amount_available
                orderproduct.save()

            else:
                orderproduct.delete()