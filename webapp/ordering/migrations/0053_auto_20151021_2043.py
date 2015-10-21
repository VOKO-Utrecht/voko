# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0052_remove_product_unit_of_measurement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productunit',
            name='abbreviations',
            field=models.CharField(help_text=b'whitespace separated', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
