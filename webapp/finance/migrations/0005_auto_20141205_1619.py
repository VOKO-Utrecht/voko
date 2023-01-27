# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_auto_20141205_1218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(related_name='payments', to='ordering.Order', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
