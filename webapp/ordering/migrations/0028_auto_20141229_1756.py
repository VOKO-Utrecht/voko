# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0027_auto_20141229_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproductcorrection',
            name='supplied_amount',
            field=models.DecimalField(max_digits=6, decimal_places=2),
            preserve_default=True,
        ),
    ]
