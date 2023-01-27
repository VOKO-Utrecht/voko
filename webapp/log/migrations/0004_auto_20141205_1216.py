# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0003_auto_20141108_1950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventlog',
            name='operator',
            field=models.ForeignKey(related_name='operator_logs', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventlog',
            name='user',
            field=models.ForeignKey(related_name='user_logs', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
