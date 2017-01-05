# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_auto_20150708_0922'),
    ]

    operations = [
        migrations.AddField(
            model_name='vokouser',
            name='is_asleep',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
