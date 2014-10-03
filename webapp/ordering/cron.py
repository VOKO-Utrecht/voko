from django.core.mail import EmailMultiAlternatives
from django.db.models.aggregates import Sum
from django.template import Context
from django.template.loader import get_template
from django_cron import CronJobBase, Schedule
from .core import get_current_order_round
from ordering.models import Supplier


class MailOrderLists(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.mail_order_lists_to_suppliers'

    def do(self):
        order_round = get_current_order_round()
        if order_round.is_open:
            return

        # To prevent mail loops
        order_round.order_placed = True
        order_round.save()

        for supplier in Supplier.objects.all():  # TODO: Only take suppliers with actual orders
            # Generate CSV
            template = get_template("ordering/admin/orderlist_per_supplier.html")
            object_list = supplier.products.\
                exclude(orderproducts=None).\
                filter(orderproducts__order__finalized=True).\
                filter(order_round=order_round).\
                annotate(amount_sum=Sum('orderproducts__amount'))

            c = Context({'object_list': object_list})
            csv = template.render(c)

            # Generate mail
            subject = 'VOKO Utrecht - Bestellijst voor %s' % order_round.collect_datetime.strftime("%d %B %Y")
            from_email = 'VOKO Utrecht <info@vokoutrecht.nl>'
            to = '%s <%s>' % (supplier.name, supplier.email)

            text_content = """
Hoi %s,

Hierbij stuur ik de bestelling van bestelronde %d
voor ons uitlevermoment op %s.

De bestelling is in CSV-formaat, dit is te openen in bijvoorbeeld Excel.

Zou je willen bevestigen als je de bestelling in goede orde hebt ontvangen?

Dit is een geautomatiseerd bericht. Reageren is gewoon mogelijk!

Vriendelijke groeten,
VOKO Utrecht
""" % (supplier, order_round.pk,  order_round.collect_datetime.strftime("%d %B %Y"))

            msg = EmailMultiAlternatives(subject, text_content, from_email,
                                         [to], cc=["VOKO Utrecht <info@vokoutrecht.nl>"])
            msg.attach('bestellijst_bestelronde_%d.csv' % order_round.pk, csv, 'text/csv')
            msg.send()