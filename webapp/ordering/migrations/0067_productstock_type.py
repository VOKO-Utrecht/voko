# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-08-12 13:55


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0066_auto_20160624_1543'),
    ]

    operations = [
        migrations.AddField(
            model_name='productstock',
            name='type',
            field=models.CharField(choices=[(b'added', b'Added'), (b'lost', b'Lost')], default=b'added', max_length=8),
        ),
    ]
