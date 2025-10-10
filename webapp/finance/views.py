from mollie.api.client import Client as MollieClient
from braces.views import LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView, View
from finance.models import Payment
from log import log_event
from ordering.core import get_current_order_round
from ordering.models import Order


def get_order_to_pay(user, is_finalized):
    cur_order_round = get_current_order_round()

    result = Order.objects.filter(paid=False,
                                  order_round=cur_order_round,
                                  user=user)
    if is_finalized is not None:
        result = result.filter(finalized=is_finalized)
    return result.last()


class MollieMixin(object):
    def __init__(self):
        self.mollie = MollieClient()
        self.mollie.set_api_key(settings.MOLLIE_API_KEY)

    def create_payment(self, amount, description, order_id):
        # Mollie API wants exactly two decimals, always
        return self.mollie.payments.create({
            'amount': {'currency': 'EUR', 'value': "{0:.2f}".format(amount)},
            'description': description,
            'method': 'ideal',
            'redirectUrl': (
                settings.BASE_URL
                + reverse("finance.confirmtransaction")
                + "?order=%s" % order_id
            ),
            'webhookUrl': settings.BASE_URL + reverse("finance.callback"),
            'metadata': {
                'order_id': order_id
            },
        })

    def get_payment(self, payment_id):
        return self.mollie.payments.get(payment_id)


class CreateTransactionView(LoginRequiredMixin, MollieMixin, FormView):
    """
    Create transaction @ bank and redirect user to bank URL
    """
    def post(self, request, *args, **kwargs):
        order_to_pay = get_order_to_pay(request.user, None)
        if not order_to_pay:
            messages.error(request, "Geen bestelling gevonden")
            return redirect(reverse('view_products'))

        log_event(event="Finalizing order %s" % order_to_pay.id, user=order_to_pay.user)
        order_to_pay.finalized = True  # Freeze order
        order_to_pay.save()

        amount_to_pay = order_to_pay\
            .total_price_to_pay_with_balances_taken_into_account()
        log_event(
            event="Initiating payment (creating transaction) for order %d "
                  "and amount %f" %
                  (order_to_pay.id, amount_to_pay), user=order_to_pay.user)

        # Extra context for debugging before starting external call
        try:
            has_succeeded_payment = order_to_pay.payments.filter(succeeded=True).exists()
        except Exception:
            has_succeeded_payment = False
        log_event(
            event=(
                "[DEBUG] Payment pre-checks for order %s" % order_to_pay.id
            ),
            user=order_to_pay.user,
            extra=(
                "finalized=%s, paid=%s, succeeded_payment_exists=%s, round_is_open=%s"
                % (
                    order_to_pay.finalized,
                    order_to_pay.paid,
                    has_succeeded_payment,
                    order_to_pay.order_round.is_open,
                )
            ),
        )

        if amount_to_pay == 0:
            log_event(
                event="Payment for order %d not necessary because order total "
                      "is %f and user's credit is %f" %
                      (order_to_pay.id, order_to_pay.total_price,
                       order_to_pay.user.balance.credit()),
                user=order_to_pay.user
            )

            self._message_payment_unnecessary()
            order_to_pay.complete_after_payment()
            return redirect(reverse('order_summary', args=(order_to_pay.pk,)))

    # Sanity checks. If one of these fails, it's very likely that someone
    # is tampering.
        assert order_to_pay.user == request.user
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False
        assert order_to_pay.payments.filter(succeeded=True).exists() is False

        if order_to_pay.order_round.is_open is not True:
            messages.error(request,
                           "De bestelronde is gesloten, "
                           "je kunt niet meer betalen.")
            log_event(
                event="Payment for order %s canceled because "
                      "order round %s is closed" %
                      (order_to_pay.id, order_to_pay.order_round.id),
                user=order_to_pay.user)
            return redirect(reverse('finish_order', args=(order_to_pay.id,)))

        # Start the payment
        try:
            results = self.create_payment(
                amount=float(amount_to_pay),
                description="VOKO Utrecht %d" % order_to_pay.id,
                order_id=order_to_pay.id,
            )
            try:
                mollie_id = results["id"]
            except Exception:
                mollie_id = getattr(results, "id", None)
            checkout_url = getattr(results, "checkout_url", None)
            status = getattr(results, "status", None)
            log_event(
                event=("[DEBUG] Mollie payment created for order %s") % order_to_pay.id,
                user=order_to_pay.user,
                extra=("mollie_id=%s, status=%s, checkout_url=%s") % (mollie_id, status, checkout_url),
            )
        except Exception as e:
            # Log and surface a friendly error to the user
            log_event(
                event=(
                    "[ERROR] Failed to create Mollie payment for order %s: %s"
                ) % (order_to_pay.id, e),
                user=order_to_pay.user,
            )
            messages.error(request, "Het aanmaken van de betaling is mislukt. Probeer het later opnieuw.")
            # Un-freeze order so user can retry
            order_to_pay.finalized = False
            order_to_pay.save()
            return redirect(reverse('finish_order', args=(order_to_pay.id,)))

        Payment.objects.create(
            amount=amount_to_pay,
            order=order_to_pay,
            mollie_id=mollie_id,
        )
        log_event(
            event=(
                "[DEBUG] Stored local Payment for order %s with mollie_id=%s"
            ) % (order_to_pay.id, mollie_id),
            user=order_to_pay.user,
        )

        redirect_url = results.checkout_url
        log_event(
            event=("[DEBUG] Redirecting user to Mollie checkout for order %s") % (order_to_pay.id),
            user=order_to_pay.user,
            extra=("checkout_url=%s") % redirect_url,
        )
        return redirect(redirect_url)

    def _message_payment_unnecessary(self):
        messages.add_message(
            self.request, messages.SUCCESS,
            'Omdat je genoeg krediet had was betalen niet nodig. '
            'Je bestelling is bevestigd.'
        )


class ConfirmTransactionView(LoginRequiredMixin, MollieMixin, TemplateView):
    """
    $bank redirects user back to this view after payment, or after payment
    was canceled.
    Transaction details are sent in GET parameters.

    Validate the payment and finish order when valid.
    """
    template_name = "finance/after_payment.html"

    def get_context_data(self, **kwargs):
        context = super(ConfirmTransactionView, self).get_context_data(
            **kwargs)

        order_id = self.request.GET.get('order')

        log_event(
            event="[DEBUG] ConfirmTransactionView called",
            user=self.request.user,
            extra=("user_id=%s, order_id=%s") % (self.request.user.id, order_id),
        )

        # Payment may already be confirmed by the webhook
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
        except Order.DoesNotExist:
            log_event(
                event=("[WARN] ConfirmTransactionView: Order not found"),
                user=self.request.user,
                extra=("user_id=%s, order_id=%s") % (self.request.user.id, order_id),
            )
            raise Http404

        if order.paid is True:
            log_event(
                event=("[DEBUG] ConfirmTransactionView: order already paid"),
                user=order.user,
                extra=("order_id=%s") % order.id,
            )
            context['payment_succeeded'] = True
            return context

        payment = Payment.objects.filter(order__id=order_id,
                                         succeeded=False,)\
            .order_by('id').last()

        if payment is None:
            log_event(
                event=("[WARN] ConfirmTransactionView: No pending Payment found"),
                user=order.user,
                extra=("order_id=%s") % order_id,
            )
            raise Http404

        log_event(
            event=("[DEBUG] ConfirmTransactionView: Fetching Mollie payment status"),
            user=order.user,
            extra=("mollie_id=%s, order_id=%s") % (payment.mollie_id, order_id),
        )
        try:
            mollie_payment = self.get_payment(payment.mollie_id)
        except Exception as e:
            log_event(
                event=("[ERROR] ConfirmTransactionView: Failed to fetch Mollie payment"),
                user=order.user,
                extra=("mollie_id=%s, order_id=%s, error=%s") % (payment.mollie_id, order_id, e),
            )
            context['payment_succeeded'] = False
            return context
        success = mollie_payment.is_paid()
        status = getattr(mollie_payment, 'status', None)
        log_event(
            event=("[DEBUG] ConfirmTransactionView: Mollie payment status fetched"),
            user=order.user,
            extra=("mollie_id=%s, status=%s, is_paid=%s") % (payment.mollie_id, status, success),
        )

        if success:
            if (payment.order.finalized is True
               and payment.order.paid is False
               and payment.order.order_round.is_open is True):

                payment.succeeded = True
                payment.save()

                payment.create_and_link_credit()
                payment.order.complete_after_payment()

                log_event(
                    event="Payment %s for order %s and amount %f succeeded" %
                          (payment.id, payment.order.id, payment.amount),
                    user=payment.order.user)

            else:
                log_event(event="Payment %s was already paid" % payment.id,
                          user=payment.order.user)

        else:
            log_event(
                event=("Payment failed in confirm view"),
                user=payment.order.user,
                extra=("payment_id=%s, order_id=%s, amount=%s, status=%s") % (payment.id, payment.order.id, payment.amount, status),
            )

        context['payment_succeeded'] = success
        return context


class PaymentWebHook(MollieMixin, View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentWebHook, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        mollie_id = request.POST.get('id')

        if not mollie_id:
            log_event(event="[WARN] Webhook called without Mollie id", user=None)
            return HttpResponse("", status=404)

        remote = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        log_event(
            event=("[DEBUG] Webhook received"),
            user=None,
            extra=("mollie_id=%s, remote=%s") % (mollie_id, remote),
        )

        try:
            payment = Payment.objects.get(mollie_id=mollie_id)
        except Payment.DoesNotExist:
            log_event(event=("[WARN] Webhook for unknown mollie_id"), user=None, extra=("mollie_id=%s") % mollie_id)
            return HttpResponse("unknown id", status=404)

        try:
            mollie_payment = self.get_payment(payment.mollie_id)
        except Exception as e:
            log_event(
                event=("[ERROR] Webhook: Failed to fetch Mollie payment"),
                user=payment.order.user,
                extra=("mollie_id=%s, order_id=%s, error=%s") % (payment.mollie_id, payment.order.id, e),
            )
            return HttpResponse("error", status=500)
        success = mollie_payment.is_paid()
        status = getattr(mollie_payment, 'status', None)
        log_event(
            event=("[DEBUG] Webhook Mollie status fetched"),
            user=payment.order.user,
            extra=("mollie_id=%s, status=%s, is_paid=%s, order_id=%s") % (payment.mollie_id, status, success, payment.order.id),
        )

        if not success:
            log_event(
                event="Payment %s for order %s and amount %f "
                      "failed via callback (Mollie status=%s)" %
                      (payment.id, payment.order.id, payment.amount, status),
                user=payment.order.user)
            return HttpResponse("")

        # Successful payment!
        payment.succeeded = True
        payment.save()

        payment.create_and_link_credit()
        log_event(
            event="Payment %s for order %s and amount %f "
                  "succeeded via callback" %
                  (payment.id, payment.order.id, payment.amount),
            user=payment.order.user)

        if payment.order.paid is False:
            # Order has not been paid, but the payment has now been confirmed
            # and credit has been created.
            # Time to finish the order, if the order round is still open.

            # Sanity Check
            assert payment.order.finalized is True

            if payment.order.order_round.is_open:
                payment.order.complete_after_payment()
            else:
                # Corner case where payment was executed before closing time,
                # but never finished (user closed browser tab),
                # the payment is now validated by callback, but order round is
                # closed and our suppliers likely have been mailed the totals.
                # Credit for the user has just been created, but we don't
                # want to complete the order because it was placed too late.
                log_event(
                    event="Order round %s is closed, so not finishing "
                          "order %s via callback!" % (
                              payment.order.order_round.id,
                              payment.order.id),
                    user=payment.order.user)

                payment.order.mail_failure_notification()

        return HttpResponse("")


class CancelPaymentView(View):
    """
    When user clicks 'cancel' on the ChooseBankView.
    """

    def get(self, request, *args, **kwargs):
        order_to_pay = get_order_to_pay(request.user, True)
        if not order_to_pay:
            messages.error(request, "Geen bestelling gevonden")
            return redirect(reverse('view_products'))

        # Sanity checks
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False

        order_to_pay.finalized = False
        order_to_pay.save()

        log_event(event="Payment for order %s canceled" % order_to_pay.id,
                  user=order_to_pay.user)

        return HttpResponseRedirect(
            reverse("finish_order", args=(order_to_pay.pk,)))
