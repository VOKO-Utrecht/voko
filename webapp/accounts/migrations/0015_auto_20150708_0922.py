# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_userprofile_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadOnlyVokoUser',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('accounts.vokouser',),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(max_length=25, blank=True),
            preserve_default=True,
        ),
    ]
