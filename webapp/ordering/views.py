from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, FormView, View, UpdateView
from django.views.generic.detail import SingleObjectMixin
import pytz
from ordering.core import get_current_order_round, get_or_create_order, get_order_product
from ordering.forms import OrderProductForm
from ordering.mails import order_confirmation_mail
from ordering.mixins import UserOwnsObjectMixin
from ordering.models import Product, OrderProduct, Order, OrderRound, Supplier


class ProductsView(LoginRequiredMixin, ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        context['current_order_round'] = get_current_order_round()
        return context


class ProductDetail(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = ProductDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ProductOrder.as_view()
        return view(request, *args, **kwargs)


class ProductDisplay(LoginRequiredMixin, DetailView):
    model = Product

    def _get_initial(self):
        order = get_or_create_order(self.request.user)
        return {'product': self.get_object().pk,
                'order': order.pk}

    def get_context_data(self, **kwargs):
        context = super(ProductDisplay, self).get_context_data(**kwargs)

        existing_op = get_order_product(product=self.get_object(),
                                        order=get_or_create_order(self.request.user))
        context['form'] = OrderProductForm(initial=self._get_initial(), instance=existing_op)
        return context


class ProductOrder(LoginRequiredMixin, SingleObjectMixin, FormView):
    model = Product
    form_class = OrderProductForm

    def get_success_url(self):
        return reverse("view_order", kwargs={'pk': get_or_create_order(self.request.user).pk})

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST, instance=get_order_product(product=self.get_object(),
                                                                   order=get_or_create_order(
                                                                       user=self.request.user
                                                                   )))
        if form.is_valid():
            order_product = form.save(commit=False)
            order_product.order = get_or_create_order(request.user)
            assert order_product.product.order_round == get_current_order_round()  # TODO: nicer error, or just disable ordering.

            # Remove product from order when amount is zero
            if order_product.amount < 1:
                if order_product.id is not None:
                    order_product.delete()
                return self.form_valid(form)

            order_product.save()
        return self.form_valid(form)


class OrderDisplay(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    # TODO: restrict to user only
    model = Order
    form_class = OrderProductForm
    success_url = "/hoera"

    def get_context_data(self, **kwargs):
        context = super(OrderDisplay, self).get_context_data(**kwargs)
        FormSet = inlineformset_factory(self.model, OrderProduct, extra=0, form=self.form_class)
        fs = FormSet(instance=self.get_object())
        context['formset'] = fs
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        FormSet = inlineformset_factory(self.model, OrderProduct, extra=0, form=self.form_class)
        fs = FormSet(instance=self.get_object(), data=request.POST)

        if self.object.finalized:
            return HttpResponseBadRequest()

        if fs.is_valid():
            fs.save()
            ## TODO: add 'succeeded' message

        # Errors are saved in formset.errors: TODO: show them in template.
        return self.render_to_response(self.get_context_data(form=self.get_form(self.form_class)))


class FinishOrder(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    template_name = "ordering/order_finish.html"
    model = Order

    def get_queryset(self):
        qs = super(FinishOrder, self).get_queryset()
        return qs.filter(finalized=False)

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        # For now, we just finish the order.
        order.place_order_and_debit()
        # order.create_and_add_payment()
        order.finalized = True
        order.save()
        return redirect('pay_order', order.pk)


class OrdersDisplay(LoginRequiredMixin, UserOwnsObjectMixin, ListView):
    """
    Overview of multiple orders
    """
    def get_queryset(self):
        return self.request.user.orders.all().order_by("-pk")


class PayOrder(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    template_name = "ordering/order_pay.html"
    model = Order

    def get_queryset(self):
        qs = super(PayOrder, self).get_queryset()
        return qs.filter(finalized=True)

    # TODO when payment works via ideal, mail after payment.
    # TODO: restrict mailing to once, even on F5
    def get(self, request, *args, **kwargs):
        product_list_text = "\n".join(["%d x %s (%s)" % (op.amount, op.product, op.product.supplier) for op in self.get_object().orderproduct_set.all()])

        amsterdam = pytz.timezone('Europe/Amsterdam')
        mail_body = order_confirmation_mail % {'first_name': request.user.first_name,
                                               'collect_datetime': self.get_object().order_round.collect_datetime.astimezone(amsterdam).strftime("%c"),
                                               'product_list': product_list_text}
        send_mail('[VOKO Utrecht] Bestelbevestiging', mail_body, 'info@vokoutrecht.nl',
                  [request.user.email], fail_silently=False)

        self.get_object()._notify_admins_about_new_order()

        return super(PayOrder, self).get(request, *args, **kwargs)


class OrderSummary(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    template_name = "ordering/order_summary.html"
    model = Order

    def get_queryset(self):
        qs = super(OrderSummary, self).get_queryset()
        return qs.filter(finalized=True)


### ADMIN VIEWS ###

class OrderRoundsAdminView(StaffuserRequiredMixin, ListView):
    model = OrderRound
    template_name = "ordering/admin/orderrounds.html"


class OrderRoundAdminView(StaffuserRequiredMixin, DetailView):
    model = OrderRound
    template_name = "ordering/admin/orderround.html"

    def _get_orders_per_supplier(self):
        data = {}
        order_round = self.get_object()
        for supplier in Supplier.objects.all():
            data[supplier] = OrderProduct.objects.filter(order__order_round=order_round,
                                                         product__supplier=supplier,
                                                         order__finalized=True)

        return data

    def get_context_data(self, **kwargs):
        context = super(OrderRoundAdminView, self).get_context_data(**kwargs)
        context['orders_per_supplier'] = self._get_orders_per_supplier()
        return context