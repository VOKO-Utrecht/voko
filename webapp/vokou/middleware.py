from ordering.core import get_current_order_round


class OrderRoundMiddleware(object):
    def process_request(self, request):
        request.current_order_round = get_current_order_round()
