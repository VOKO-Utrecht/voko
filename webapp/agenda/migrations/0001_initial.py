# Generated by Django 3.2.20 on 2023-09-08 18:43

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0032_alter_userprofile_shares_car'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransientEvent',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150, verbose_name='titel')),
                ('short_description', models.CharField(blank=True, max_length=300, null=True, verbose_name='korte beschrijving')),
                ('long_description', tinymce.models.HTMLField(blank=True, null=True, verbose_name='lange beschrijving')),
                ('date', models.DateField(default=datetime.datetime.now, verbose_name='datum')),
                ('time', models.TimeField(default=datetime.datetime.now, verbose_name='tijd')),
                ('is_shift', models.BooleanField(default=False)),
                ('org_model', models.CharField(blank=True, max_length=50, null=True)),
                ('org_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PersistentEvent',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150, verbose_name='titel')),
                ('short_description', models.CharField(blank=True, max_length=300, null=True, verbose_name='korte beschrijving')),
                ('long_description', tinymce.models.HTMLField(blank=True, null=True, verbose_name='lange beschrijving')),
                ('date', models.DateField(default=datetime.datetime.now, verbose_name='datum')),
                ('time', models.TimeField(default=datetime.datetime.now, verbose_name='tijd')),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.address')),
            ],
            options={
                'verbose_name': 'evenement',
                'verbose_name_plural': 'evenementen',
                'abstract': False,
                'managed': True,
            },
        ),
    ]
