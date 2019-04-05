import io

from datetime import datetime
import pytz
from django.core.mail import EmailMultiAlternatives
from django.db.models.aggregates import Sum
from django_cron import CronJobBase, Schedule

from log import log_event
from .core import get_current_order_round, get_next_order_round
from ordering.models import Supplier
import unicodecsv as csv


def fix_decimal_separator(decimal_value):
    # Because DECIMAL_SEPARATOR is being ignored :(
    return str(decimal_value).replace('.', ',')


class SendOrderReminders(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.send_order_reminders'

    def do(self):
        order_round = get_current_order_round()
        print(("Order round: %s" % order_round))

        if not order_round.is_open:
            print("Order round is closed")
            return

        current_datetime = datetime.now(pytz.utc)
        closing_delta = order_round.closed_for_orders - current_datetime
        hours_before_closing = int(closing_delta.total_seconds() / 60 / 60)
        print("Hours before closing (rounded): %s" % hours_before_closing)

        if ((hours_before_closing <=
             order_round.reminder_hours_before_closing)
                and order_round.reminder_sent is False):
            print("Sending reminders!")
            order_round.send_reminder_mails()


class MailOrderLists(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.mail_order_lists_to_suppliers'

    def do(self):
        order_round = get_current_order_round()
        print(("Order round: %s" % order_round))
        if order_round.is_open:
            print("Order round is closed")
            return

        if order_round.is_not_open_yet():
            print("Order round is not open yet")
            return

        if order_round.order_placed:
            print("Order has already been placed")
            return

        # To prevent mail loops
        order_round.order_placed = True
        order_round.save()

        for supplier in Supplier.objects.all():
            if not supplier.has_orders_in_current_order_round():
                print(("No orders for supplier %s" % supplier))
                log_event(event="Supplier %s has no orders in current round, "
                                "so not sending order list." % supplier)
                continue

            print(("Generating lists for supplier %s" % supplier))

            # Generate CSV
            in_mem_file = io.BytesIO()
            csv_writer = csv.writer(in_mem_file, delimiter=';', quotechar='|')

            # Write header row
            csv_writer.writerow(
                ["Aantal", "Eenheid", "Product", "Omschrijving",
                 "Inkoopprijs Euro", "Subtotaal"])

            ordered_products = supplier.products. \
                exclude(orderproducts=None). \
                filter(orderproducts__order__paid=True). \
                filter(order_round=order_round). \
                annotate(amount_sum=Sum('orderproducts__amount'))

            if not ordered_products:
                log_event(event="Supplier %s has only STOCK orders "
                                "in current round, "
                                "so not sending order list." % supplier)
                continue

            # Write products and amounts
            for obj in ordered_products:
                csv_writer.writerow([
                    fix_decimal_separator(obj.amount_sum),
                    obj.unit_of_measurement,
                    obj.name,
                    obj.description.replace("\n", " ").replace("\r", " "),
                    # TODO make sure newlines aren't stored
                    # in our products
                    fix_decimal_separator(obj.base_price),
                    fix_decimal_separator(obj.amount_sum * obj.base_price)
                ])

            # Write 'total' row
            total = fix_decimal_separator(sum(
                [obj.amount_sum * obj.base_price for obj in ordered_products]))
            csv_writer.writerow([])
            csv_writer.writerow(["TOTAAL", "", "", "", "", total])

            in_mem_file.seek(0)
            in_mem_file.seek(0)  # Why is this here twice?

            # Generate mail
            subject = ('VOKO Utrecht - Bestellijst voor %s' %
                       order_round.collect_datetime.strftime("%d %B %Y"))
            from_email = 'VOKO Utrecht Boerencontact <boeren@vokoutrecht.nl>'
            to = '%s <%s>' % (supplier.name, supplier.email)

            text_content = """
Hoi %s,

Hierbij sturen we onze bestelling voor bestelronde %d
voor ons uitlevermoment op %s.

De bestelling is in CSV-formaat, dit is te openen in bijvoorbeeld Excel.

Dit is een geautomatiseerd bericht, maar reageren is gewoon mogelijk.

Vriendelijke groeten,
VOKO Utrecht
""" % (
                supplier,
                order_round.pk,
                order_round.collect_datetime.strftime("%d %B %Y")
            )

            msg = EmailMultiAlternatives(
                subject,
                text_content,
                from_email,
                [to],
                cc=["VOKO Utrecht Boerencontact <boeren@vokoutrecht.nl>"]
            )

            msg.attach('voko_utrecht_bestelling_ronde_%d.csv' % order_round.pk,
                       in_mem_file.read().decode("utf-8"), 'text/csv')
            msg.send()


class SendRideMails(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.send_ride_mails'

    def do(self):
        order_round = get_current_order_round()
        print("Order round: %s" % order_round)

        if order_round.is_over and order_round.rides_mails_sent is False:
            print("Sending ride mails!")
            order_round.send_ride_mails()


class SendPrepareRideMails(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ordering.send_prepare_ride_mails'

    def do(self):
        print("SendPrepareRideMails")
        order_round = get_current_order_round()
        print("Order round: %s" % order_round)
        if order_round.is_open:
            next_order_round = get_next_order_round()
            print("Next order round: %s" % next_order_round)
            if (next_order_round is not None and
                    next_order_round.prepare_ride_mails_sent is False):
                print("Sending prepare ride mails!")
                next_order_round.send_prepare_ride_mails()
