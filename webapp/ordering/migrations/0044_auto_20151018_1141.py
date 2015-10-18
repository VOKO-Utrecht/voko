# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0043_orderproductcorrection_charge_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit_amount',
            field=models.IntegerField(default=1, help_text=b'e.g. if half a kilo: "500"'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_of_measurement',
            field=models.CharField(help_text=b'e.g. if half a kilo: "Gram"', max_length=10, choices=[(b'Stuk', b'Stuk'), (b'Gram', b'Gram'), (b'Decagram', b'Decagram (10g)'), (b'Hectogram', b'Hectogram (100g)'), (b'Half pond', b'Half pond (250g)'), (b'Pond', b'Pond (500g)'), (b'Kilogram', b'Kilogram'), (b'5 Kilogram', b'5 Kilogram'), (b'Deciliter', b'Deciliter (100ml)'), (b'Liter', b'Liter')]),
            preserve_default=True,
        ),
    ]
