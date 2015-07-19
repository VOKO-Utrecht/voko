# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0038_auto_20150707_1856'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='debit',
            field=models.OneToOneField(related_name='order', null=True, blank=True, to='finance.Balance'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='orderproductcorrection',
            name='credit',
            field=models.OneToOneField(related_name='correction', to='finance.Balance'),
            preserve_default=True,
        ),
    ]
