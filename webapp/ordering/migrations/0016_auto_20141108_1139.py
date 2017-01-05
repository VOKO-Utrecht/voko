# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0015_auto_20141108_1138'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': b'Bestelling', 'verbose_name_plural': b'Bestellingen'},
        ),
        migrations.AlterModelOptions(
            name='orderproduct',
            options={'verbose_name': b'Productbestelling', 'verbose_name_plural': b'Productbestellingen'},
        ),
        migrations.AlterModelOptions(
            name='orderproductcorrection',
            options={'verbose_name': b'Productbestelling-correctie', 'verbose_name_plural': b'Productbestelling-correcties'},
        ),
        migrations.AlterModelOptions(
            name='orderround',
            options={'verbose_name': b'Bestelronde', 'verbose_name_plural': b'Bestelronden'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': b'Product', 'verbose_name_plural': b'Producten'},
        ),
        migrations.AlterModelOptions(
            name='supplier',
            options={'verbose_name': b'Leverancier'},
        ),
        migrations.AddField(
            model_name='orderround',
            name='suppliers_reminder_sent',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
