# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0025_auto_20141208_2043'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplierorder',
            name='order_round',
        ),
        migrations.RemoveField(
            model_name='supplierorder',
            name='products',
        ),
        migrations.RemoveField(
            model_name='supplierorderproduct',
            name='order',
        ),
        migrations.DeleteModel(
            name='SupplierOrder',
        ),
        migrations.RemoveField(
            model_name='supplierorderproduct',
            name='product',
        ),
        migrations.DeleteModel(
            name='SupplierOrderProduct',
        ),
    ]
