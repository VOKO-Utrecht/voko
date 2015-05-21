# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0034_auto_20150514_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='draftproduct',
            name='is_valid',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='draftproduct',
            name='validation_error',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
