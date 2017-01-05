# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0051_auto_20151018_1444'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='unit_of_measurement',
        ),
    ]
