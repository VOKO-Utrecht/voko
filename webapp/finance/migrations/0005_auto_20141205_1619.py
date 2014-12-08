# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_auto_20141205_1218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(related_name='payments', to='ordering.Order', null=True),
            preserve_default=True,
        ),
    ]