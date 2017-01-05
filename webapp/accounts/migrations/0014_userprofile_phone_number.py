# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_auto_20141205_1216'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
    ]
