# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0026_auto_20141214_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproductcorrection',
            name='order_product',
            field=models.OneToOneField(related_name='correction', to='ordering.OrderProduct', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
