# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0036_remove_product_minimum_total_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderround',
            name='suppliers_reminder_sent',
        ),
    ]
