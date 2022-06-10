# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0002_auto_20141011_2146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventlog',
            name='operator',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
    ]
