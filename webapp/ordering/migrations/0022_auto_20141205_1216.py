# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0021_auto_20141205_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_round',
            field=models.ForeignKey(related_name='orders', to='ordering.OrderRound'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(related_name='orders', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='order',
            field=models.ForeignKey(related_name='orderproducts', to='ordering.Order'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='orderproduct',
            name='product',
            field=models.ForeignKey(related_name='orderproducts', to='ordering.Product'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='order_round',
            field=models.ForeignKey(related_name='products', to='ordering.OrderRound'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(related_name='products', to='ordering.Supplier'),
            preserve_default=True,
        ),
    ]
