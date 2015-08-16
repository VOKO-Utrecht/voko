# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_vokouser_is_asleep'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vokouser',
            name='is_asleep',
            field=models.BooleanField(default=False, verbose_name=b'Sleeping (inactive) member'),
            preserve_default=True,
        ),
    ]
