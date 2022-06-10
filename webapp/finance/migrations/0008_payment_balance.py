# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_auto_20150719_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='balance',
            field=models.OneToOneField(related_name='payment', null=True, to='finance.Balance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
