# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0009_auto_20160304_1511'),
        ('ordering', '0054_remove_order_debit'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='debit',
            field=models.OneToOneField(related_name='order', null=True, blank=True, to='finance.Balance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
