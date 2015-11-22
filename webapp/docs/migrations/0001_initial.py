# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to=b'docs/%Y/%m/%d')),
                ('slug', models.SlugField(unique=True, max_length=100, editable=False)),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documenten',
            },
            bases=(models.Model,),
        ),
    ]
