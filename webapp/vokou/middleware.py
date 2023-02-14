from ordering.core import get_current_order_round


class OrderRoundMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        request.current_order_round = get_current_order_round()

        response = self.get_response(request)
        return response
