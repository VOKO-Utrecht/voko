# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0044_auto_20151018_1141'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('abbreviations', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Producteenheid',
                'verbose_name_plural': 'Producteenheden',
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_of_measurement',
            field=models.CharField(help_text=b'e.g. if half a kilo: "Gram"', max_length=10, choices=[(b'Stuk', b'Stuk'), (b'Bosje', b'Bosje'), (b'Gram', b'Gram'), (b'Decagram', b'Decagram (10g)'), (b'Hectogram', b'Hectogram (100g)'), (b'Half pond', b'Half pond (250g)'), (b'Pond', b'Pond (500g)'), (b'Kilogram', b'Kilogram'), (b'5 Kilogram', b'5 Kilogram'), (b'Deciliter', b'Deciliter (100ml)'), (b'Liter', b'Liter')]),
            preserve_default=True,
        ),
    ]
