# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_auto_20141205_1619'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='user',
        ),
    ]
