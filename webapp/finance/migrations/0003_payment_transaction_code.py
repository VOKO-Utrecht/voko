# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_auto_20141203_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='transaction_code',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
