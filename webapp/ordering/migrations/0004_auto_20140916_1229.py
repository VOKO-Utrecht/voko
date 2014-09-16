# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0003_auto_20140915_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderround',
            name='collect_datetime',
            field=models.DateTimeField(default=datetime.date(2014, 9, 16)),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='orderround',
            name='collect_date',
        ),
        migrations.AlterField(
            model_name='orderround',
            name='closed_for_orders',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='orderround',
            name='open_for_orders',
            field=models.DateTimeField(),
        ),
    ]
