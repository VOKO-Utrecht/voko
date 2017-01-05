# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0030_auto_20150126_2007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='collected',
        ),
    ]
