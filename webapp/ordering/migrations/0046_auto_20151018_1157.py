# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0045_auto_20151018_1154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productunit',
            name='abbreviations',
            field=models.CharField(help_text=b'whitespace separated', max_length=255),
            preserve_default=True,
        ),
    ]
