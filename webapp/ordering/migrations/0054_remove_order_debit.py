# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0053_auto_20151021_2043'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='debit',
        ),
    ]
