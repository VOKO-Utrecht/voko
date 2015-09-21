from braces.views import GroupRequiredMixin
from django.views.generic import ListView
from ordering.models import OrderRound, OrderProductCorrection


class RoundsPerYearView(GroupRequiredMixin, ListView):
    template_name = "finance/admin/specified.html"
    group_required = "Admin"

    def get_queryset(self):
        # return order rounds that *opened* in $year
        return OrderRound.objects.filter(open_for_orders__year=self.kwargs['year']).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(RoundsPerYearView, self).get_context_data(**kwargs)
        context['year'] = self.kwargs['year']
        context['suppliers_data'] = self.compose_table_data()
        context['totals'] = self.get_order_totals_per_round()
        return context

    def compose_table_data(self):
        ret = []

        for rnd in self.get_queryset():
            for supplier in rnd.suppliers():
                d = dict()
                d['round'] = rnd
                d['supplier'] = supplier
                d['total_amount'] = rnd.total_order_amount_per_supplier(supplier)

                corrections = OrderProductCorrection.objects.filter(order_product__order__order_round=rnd,
                                                                    order_product__product__supplier=supplier)
                d['supplier_corrections_exc'] = sum([c.calculate_supplier_refund()
                                                     for c in corrections.filter(charge_supplier=True)])
                d['supplier_corrections_inc'] = sum([c.calculate_refund()
                                                     for c in corrections.filter(charge_supplier=True)])
                d['voko_corrections_inc'] = sum([c.calculate_refund()
                                                for c in corrections.filter(charge_supplier=False)])

                d['to_pay'] = d['total_amount'] - d['supplier_corrections_exc']
                ret.append(d)

        return ret

    def get_order_totals_per_round(self):
        for rnd in self.get_queryset():
            yield {rnd: rnd.total_order_amount()}
