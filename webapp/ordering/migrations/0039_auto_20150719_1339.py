# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0039_auto_20150717_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='debit',
            field=models.OneToOneField(related_name='order', null=True, blank=True, to='finance.Balance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='orderproductcorrection',
            name='credit',
            field=models.OneToOneField(related_name='correction', to='finance.Balance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
