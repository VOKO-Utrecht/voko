# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def link_balances(apps, schema_editor):
    # Link Balance objects which are payments to their Payment objects
    Payment = apps.get_model("finance", "Payment")
    Balance = apps.get_model("finance", "Balance")

    for p in Payment.objects.filter(succeeded=True):
        print "============="
        print "Payment: ID %s, AMOUNT %s" % (p.id, p.amount)
        order = p.order
        print "Order: ID %s" % order.id
        balance = order.debit

        if balance is None:
            print "Order has no debit linked, finding a match"
            balance = Balance.objects.get(
                user=order.user,
                type="CR",
                notes__endswith="#%s" % order.id
            )

        print "Linking to Balance: ID %s, AMOUNT %s, NOTES: %s" % (balance.id, balance.amount, balance.notes)
        p.balance = balance
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0008_payment_balance'),
        ('ordering', '0053_auto_20151021_2043')
    ]

    operations = [
        migrations.RunPython(link_balances)
    ]
