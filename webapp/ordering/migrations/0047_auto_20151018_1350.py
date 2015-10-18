# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_initial_units(apps, schema_editor):
    ProductUnit = apps.get_model("ordering", "ProductUnit")
    ProductUnit.objects.create(
        name='Stuk',
        description='Stuk',
        abbreviations='st, stk'
    )
    ProductUnit.objects.create(
        name='Bosje',
        description='Bosje',
        abbreviations='bos'
    )
    ProductUnit.objects.create(
        name='Gram',
        description='Gram',
        abbreviations='g gr'
    )
    ProductUnit.objects.create(
        name='Decagram',
        description='Decagram (10g)',
        abbreviations='dg'
    )
    ProductUnit.objects.create(
        name='Hectogram',
        description='Hectogram (100g)',
        abbreviations='hg'
    )
    ProductUnit.objects.create(
        name='Half pond',
        description='Half pond (250g)',
        abbreviations=''
    )
    ProductUnit.objects.create(
        name='Pond',
        description='Pond (500g)',
        abbreviations=''
    )
    ProductUnit.objects.create(
        name='Kilogram',
        description='Kilogram (1000g)',
        abbreviations='kg k'
    )
    ProductUnit.objects.create(
        name='Milliliter',
        description='Milliliter',
        abbreviations='ml cc'
    )
    ProductUnit.objects.create(
        name='Centiliter',
        description='Centiliter (10ml)',
        abbreviations='cl'
    )
    ProductUnit.objects.create(
        name='Deciliter',
        description='Deciliter (100ml)',
        abbreviations='dl'
    )
    ProductUnit.objects.create(
        name='Liter',
        description='Liter',
        abbreviations='l ltr'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0046_auto_20151018_1157'),
    ]

    operations = [
        migrations.RunPython(add_initial_units)
    ]
