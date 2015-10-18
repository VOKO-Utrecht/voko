# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0050_auto_20151018_1435'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='temp_unit',
            new_name='unit',
        ),
    ]
