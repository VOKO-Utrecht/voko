# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0031_remove_order_collected'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user_notes',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
