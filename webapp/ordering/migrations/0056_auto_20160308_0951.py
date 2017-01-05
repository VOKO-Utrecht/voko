# -*- coding: utf-8 -*-


from django.db import models, migrations


def link_debits_to_orders(apps, schema_editor):
    Order = apps.get_model("ordering", "Order")
    Balance = apps.get_model("finance", "Balance")

    orders = Order.objects.filter(
        finalized=True,
        paid=True
    )

    for o in orders:
        print("======")
        print(("Order %s" % o.id))

        # exceptions (manually created debit objects)
        if o.id == 105:
            o.debit = Balance.objects.get(id=134)
        if o.id == 788:
            o.debit = Balance.objects.get(id=845)
        if o.id == 931:
            o.debit = Balance.objects.get(id=985)

        if not o.debit:
            try:
                o.debit = Balance.objects.get(user=o.user,
                                              type="DR",
                                              notes__endswith="for Order %s" % o.id)
            except Balance.DoesNotExist:
                o.debit = Balance.objects.get(user=o.user,
                                              type="DR",
                                              notes__endswith="voor bestelling #%s" % o.id)

        o.save()
        print(("Linking to Balance: ID %s, AMOUNT %s, NOTES: %s" % (o.debit.id, o.debit.amount, o.debit.notes)))

    print("Done!")


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0055_order_debit'),
    ]

    operations = [
        migrations.RunPython(link_debits_to_orders)
    ]
