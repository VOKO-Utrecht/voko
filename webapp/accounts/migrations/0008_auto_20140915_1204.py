# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20140915_1118'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name': b'adres', 'verbose_name_plural': b'adressen'},
        ),
        migrations.AlterModelOptions(
            name='emailconfirmation',
            options={'verbose_name': b'emailbevestiging', 'verbose_name_plural': b'emailbevestigingen'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': b'ledenprofiel', 'verbose_name_plural': b'ledenprofielen'},
        ),
        migrations.AlterModelOptions(
            name='vokouser',
            options={'verbose_name': b'lid', 'verbose_name_plural': b'leden'},
        ),
    ]
