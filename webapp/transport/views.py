from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView)
from transport import models
from ordering.models import OrderRound, Supplier
from django.db.models import Q
import datetime
from transport.mixins import UserIsInvolvedMixin


class Schedule(LoginRequiredMixin, ListView):
    template_name = "transport/schedule.html"

    def get_queryset(self):
        user = self.request.user

        if (user.groups.filter(name='Transportcoordinatoren').exists()):
            rides = models.Ride.objects.all()
        else:
            rides = models.Ride.objects.filter(
                Q(driver=user) |
                Q(codriver=user) |
                Q(coordinators__id__exact=user.id)
            )

        return rides.filter(
            order_round__collect_datetime__gte=datetime.date.today()
        ).order_by("-id")


class Ride(LoginRequiredMixin, UserIsInvolvedMixin, DetailView):
    template_name = "transport/ride.html"
    model = models.Ride

    def _get_orders_per_supplier(self):
        data = {}
        ride = self.get_object()
        order_round = ride.order_round
        for supplier in Supplier.objects.all():
            suppliers_products_this_round = supplier.products.filter(
                order_round=order_round)

            if len(suppliers_products_this_round) == 0:
                continue

            data[supplier] = []

            for product in suppliers_products_this_round:
                order_products = product.orderproducts.filter(order__paid=True)
                product_sum = sum([op.amount for op in order_products])
                if product_sum == 0:
                    continue

                data[supplier].append(
                    {'product': product,
                    'amount': product_sum}
                )

        return data

    def get_context_data(self, **kwargs):
        context = super(Ride, self).get_context_data(**kwargs)
        context['orders_per_supplier'] = self._get_orders_per_supplier()
        return context
