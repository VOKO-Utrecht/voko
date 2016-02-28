from braces.views import GroupRequiredMixin
from django.http import HttpResponse
from django.views.generic import View, TemplateView
from ordering.models import OrderRound, OrderProductCorrection
import simplejson as json  # Decimal support
from collections import OrderedDict


class JsonRoundOverview(GroupRequiredMixin, View):
    group_required = "Admin"

    def get(self, request, round_id):
        round = OrderRound.objects.get(id=round_id)
        data = self.gather_data(round)
        return HttpResponse(json.dumps(data), content_type="application/json")

    def gather_data(self, round):
        ret = {'suppliers': OrderedDict()}

        for supplier in round.suppliers():
            d = dict()
            d['total_amount'] = round.total_order_amount_per_supplier(supplier)

            corrections = OrderProductCorrection.objects.filter(order_product__order__order_round=round,
                                                                order_product__product__supplier=supplier)
            d['supplier_corrections_exc'] = sum([c.calculate_supplier_refund()
                                                 for c in corrections.filter(charge_supplier=True)])
            d['voko_corrections_inc'] = sum([c.calculate_refund()
                                            for c in corrections.filter(charge_supplier=False)])

            d['to_pay'] = d['total_amount'] - d['supplier_corrections_exc']
            ret['suppliers'][supplier.name] = d

        ret['total_profit'] = round.total_profit()

        return ret


class RoundOverview(GroupRequiredMixin, TemplateView):
    group_required = "Admin"
    template_name = "finance/admin/round_overview.html"

    def get_context_data(self, round_id, **kwargs):
        ctx = super(RoundOverview, self).get_context_data(**kwargs)
        ctx['round_id'] = round_id
        return ctx


class YearOverview(GroupRequiredMixin, TemplateView):
    group_required = "Admin"
    template_name = "finance/admin/year_overview.html"

    def get_context_data(self, year, **kwargs):
        ctx = super(YearOverview, self).get_context_data(**kwargs)
        ctx['year'] = year
        ctx['rounds'] = OrderRound.objects.filter(
            open_for_orders__year=self.kwargs['year']).order_by('-id')  # Rounds that opened in :year:

        return ctx