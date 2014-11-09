import csv
from django.core.management.base import BaseCommand
from ordering.core import get_current_order_round
from ordering.models import Product, Supplier


class Command(BaseCommand):
    args = '<Supplier name> <Path to CSV>'
    help = 'Create product objects from CSV'

    def add_arguments(self, parser):
        parser.add_argument('--csvfile', type=str)

    def handle(self, *args, **options):
        supplier = Supplier.objects.get(name=args[0])
        csvfile = args[1]

        print "============="
        print "Supplier: %s" % supplier
        print "CSV file: %s" % csvfile
        print "============="

        data = []
        order_round = get_current_order_round()

        with open(csvfile, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                # Productnaam | Omschrijving (optioneel) | Verkoopeenheid | Prijs per eenheid in Euro | Maximaal leverbaar | Minimale leverhoeveelheid
                try:
                    name, description, unit, price, maximum, minimum = row

                    if maximum.lower() == 'onbeperkt':
                        maximum = None

                    if minimum.lower() == 'onbeperkt':
                        minimum = None

                    maximum = int(maximum) if maximum else None
                    minimum = int(minimum) if minimum else None

                    # Strip off euro sign
                    if not price.isdigit():
                        price = price[3:]
                    price = float(price)
                    # print "PRICE: %s -> %s" % (old_price, price)

                    # Decide on unit
                    for u, _ in Product.UNITS:
                        if u in unit:
                            unit = u

                    product = Product(
                        name=name,
                        description=description,
                        base_price=price,
                        supplier=supplier,
                        order_round=order_round,
                        minimum_total_order=minimum,
                        maximum_total_order=maximum,
                        unit_of_measurement=unit,
                    )

                    data.append((row, product))

                except ValueError as e:
                    print "VALUEERROR ON ROW: %s" % row
                    print e

            for d in data:
                print "====="
                print d[0]
                for field in ("name", "description", "base_price", "minimum_total_order",
                              "maximum_total_order", "unit_of_measurement"):
                    print "%s: %s" % (field, getattr(d[1], field))
                do_save = raw_input("Save? [Y/n] > ")
                if do_save == "y" or do_save == "":
                    print "Saving"
                    d[1].save()
                else:
                    print "Not saving"