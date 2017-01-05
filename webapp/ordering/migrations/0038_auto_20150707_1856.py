# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0037_remove_orderround_suppliers_reminder_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderround',
            name='order_placed',
            field=models.BooleanField(default=False, editable=False),
            preserve_default=True,
        ),
    ]
