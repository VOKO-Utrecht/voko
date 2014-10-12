# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0011_auto_20141011_2146'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': b'Bestelling', 'verbose_name_plural': b'Bestellingen'},
        ),
        migrations.AlterModelOptions(
            name='orderproduct',
            options={'verbose_name': b'Productbestelling', 'verbose_name_plural': b'Productbestellingen'},
        ),
        migrations.AlterModelOptions(
            name='orderproductcorrection',
            options={'verbose_name': b'Productbestelling-correctie', 'verbose_name_plural': b'Productbestelling-correcties'},
        ),
        migrations.AlterModelOptions(
            name='orderround',
            options={'verbose_name': b'Bestelronde', 'verbose_name_plural': b'Bestelronden'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': b'Product', 'verbose_name_plural': b'Producten'},
        ),
        migrations.AlterModelOptions(
            name='supplier',
            options={'verbose_name': b'Leverancier'},
        ),
        migrations.AddField(
            model_name='supplier',
            name='biography',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
