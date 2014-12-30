# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0028_auto_20141229_1756'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproductcorrection',
            name='supplied_amount',
        ),
        migrations.AddField(
            model_name='orderproductcorrection',
            name='supplied_percentage',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
