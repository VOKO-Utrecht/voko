# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='maximum_total_order',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
