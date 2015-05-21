# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0035_auto_20150515_1336'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='minimum_total_order',
        ),
    ]
