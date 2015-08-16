# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_auto_20150816_1514'),
    ]

    operations = [
        migrations.CreateModel(
            name='SleepingVokoUser',
            fields=[
            ],
            options={
                'verbose_name': 'Slapend lid',
                'proxy': True,
                'verbose_name_plural': 'Slapende leden',
            },
            bases=('accounts.vokouser',),
        ),
        migrations.AlterModelOptions(
            name='readonlyvokouser',
            options={'verbose_name': 'Lid (read-only)', 'verbose_name_plural': 'Leden (read-only)'},
        ),
    ]
