# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0005_supplier_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderround',
            name='order_placed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
