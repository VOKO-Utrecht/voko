# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0042_product_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderproductcorrection',
            name='charge_supplier',
            field=models.BooleanField(default=True, verbose_name=b'Charge expenses to supplier'),
            preserve_default=True,
        ),
    ]
