from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models.aggregates import Sum
from django.template import Context
from django.template.loader import get_template
from django_cron import CronJobBase, Schedule
from .core import get_current_order_round
from log import log_event
from mailing.helpers import render_mail_template
from mailing.models import MailTemplate
from ordering.models import Supplier


class SendReminderMailToSuppliersCron(CronJobBase):
    RUN_AT_TIMES = ['10:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'ordering.send_reminder_mail_to_suppliers'

    MAIL_TEMPLATE_ID = 8
    DAYS_PRIOR = 3

    def do(self):
        order_round = get_current_order_round()

        # Order round should not be open yet as we're reminding suppliers about it
        if not order_round.is_not_open_yet():
            return

        # Send X days before order round opens
        date_to_send = (order_round.open_for_orders - timedelta(days=self.DAYS_PRIOR)).date()
        date_today = datetime.today().date()
        if date_to_send != date_today:
            return

        # Check send state
        if order_round.suppliers_reminder_sent:
            return

        # Better to fail than to keep mailing. Set flag before action.
        order_round.suppliers_reminder_sent = True
        order_round.save()

        # Create mail for every supplier
        mail_template = MailTemplate.objects.get(id=self.MAIL_TEMPLATE_ID)

        for supplier in Supplier.objects.all():
            subject, html_message, plain_message = render_mail_template(mail_template,
                                                                        order_round=order_round,
                                                                        supplier=supplier)
            send_mail(subject=subject,
                      message=plain_message,
                      from_email="VOKO Utrecht <info@vokoutrecht.nl>",
                      recipient_list=["%s <%s>" % (supplier.name, supplier.email)],
                      html_message=html_message)

            log_event(event="Herinneringsmail naar %s" % supplier.name,
                      extra=html_message)


class MailOrderLists(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.mail_order_lists_to_suppliers'

    def do(self):
        order_round = get_current_order_round()
        if order_round.is_open:
            return

        if order_round.is_not_open_yet():
            return

        if order_round.order_placed:
            return

        # To prevent mail loops
        order_round.order_placed = True
        order_round.save()

        for supplier in Supplier.objects.all():
            if not supplier.has_orders_in_current_order_round():
                continue

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

Dit is een geautomatiseerd bericht. Reageren is gewoon mogelijk!

Vriendelijke groeten,
VOKO Utrecht
""" % (supplier, order_round.pk,  order_round.collect_datetime.strftime("%d %B %Y"))

            msg = EmailMultiAlternatives(subject, text_content, from_email,
                                         [to], cc=["VOKO Utrecht <info@vokoutrecht.nl>"])
            msg.attach('bestellijst_bestelronde_%d.csv' % order_round.pk, csv, 'text/csv')
            msg.send()