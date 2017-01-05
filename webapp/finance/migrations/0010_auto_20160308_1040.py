# -*- coding: utf-8 -*-


from django.db import migrations


def link_balances_to_payments(apps, _):
    Balance = apps.get_model("finance", "Balance")
    Payment = apps.get_model("finance", "Payment")

    for p in Payment.objects.filter(succeeded=True):
        print("======")
        print(("Payment %s, amount %s" % (p.id, p.amount)))

        # exceptions
        if p.id == 44:
            p.balance = Balance.objects.get(id=313)

        if not p.balance:
            try:
                p.balance = Balance.objects.get(user=p.order.user,
                                                amount=p.amount,
                                                notes="Bestelling #%s contant betaald" % p.order.id)
            except Balance.DoesNotExist:
                p.balance = Balance.objects.get(user=p.order.user,
                                                amount=p.amount,
                                                notes="iDeal betaling voor bestelling #%s" % p.order.id)

        p.save()
        print(("Linking to Balance: ID %s, AMOUNT %s, NOTES: %s" % (p.balance.id, p.balance.amount, p.balance.notes)))

    print("Done!")


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0009_auto_20160304_1511'),
    ]

    operations = [
        migrations.RunPython(link_balances_to_payments)
    ]
