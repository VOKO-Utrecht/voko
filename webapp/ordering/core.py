from ordering.models import OrderRound


def get_current_order_round():
    ## TODO: Get current order round based on current date
    ## If non existing, get_or_create?
    return list(OrderRound.objects.all())[-1]