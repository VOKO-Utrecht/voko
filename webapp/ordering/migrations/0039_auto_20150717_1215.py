# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0038_auto_20150707_1856'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='finalized',
            new_name='paid',
        ),
    ]
