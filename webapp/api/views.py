from braces.views import LoginRequiredMixin
from django.views.generic import View
from ordering.models import OrderRound
from pytz import UTC
from datetime import datetime
from .utils import CSVResponse, JSONResponse
from accounts.models import VokoUser


class OrdersAPIView(LoginRequiredMixin, View):
    def get_raw_data(self):
        now = datetime.now(UTC)
        data = []
        order_rounds = OrderRound.objects.all() \
            .filter(closed_for_orders__lt=now) \
            .order_by("open_for_orders")
        for order_round in order_rounds:
            products = order_round.products.all()
            suppliers = set()
            for product in products:
                suppliers.add(product.supplier.name)
            paid_orders = order_round.orders.filter(paid=True)
            ordering_members = set()
            for order in paid_orders:
                ordering_members.add(order.user.id)
            members = VokoUser.objects \
                .filter(created__lt=order_round.open_for_orders)

            data.append({
                'open_for_orders_date': order_round.open_for_orders.date(),
                'number_of_orders': order_round.number_of_orders(),
                'number_of_ordering_members': len(ordering_members),
                'number_of_members': members.count(),
                'total_revenue': order_round.total_revenue(),
                'number_of_products': products.count(),
                'numbers_of_suppliers': len(suppliers),
                'markup_percentage': order_round.markup_percentage
            })
        return data


class OrdersJSONView(OrdersAPIView):
    def get(self, request, *args, **kwargs):
        return JSONResponse(self.get_raw_data())


class OrdersCSVView(OrdersAPIView):
    def get(self, request):
        return CSVResponse(self.get_raw_data())


class AccountsAPIView(LoginRequiredMixin, View):
    def get_raw_data(self):
        data = []
        users = VokoUser.objects.all()
        for user in users:
            field = {
                'created_date': user.created.date(),  # rounded to day
                'is_active': user.is_active,
                'is_asleep': user.is_asleep,
            }

            email_confirmation = user.email_confirmation
            if email_confirmation.is_confirmed:
                field['confirmed_date'] = email_confirmation.modified.date()

            paid_orders = user.orders.filter(paid=True).order_by("modified")
            first_paid_order = paid_orders.first()
            if first_paid_order:
                field['first_order_date'] = first_paid_order.modified.date()

            data.append(field)
        return data


class AccountsJSONView(AccountsAPIView):
    def get(self, request, *args, **kwargs):
        return JSONResponse(self.get_raw_data())


class AccountsCSVView(AccountsAPIView):
    def get(self, request):
        return CSVResponse(self.get_raw_data())
