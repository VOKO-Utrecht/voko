# Generated by Django 3.2.20 on 2023-09-02 08:28

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
            name='Event',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150)),
                ('short_description', tinymce.models.HTMLField(blank=True, null=True)),
                ('long_description', tinymce.models.HTMLField(blank=True, null=True)),
                ('date_time', models.DateTimeField(default=datetime.datetime.now)),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.address')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PersistentEvent',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='agenda.event')),
            ],
            options={
                'verbose_name': 'evenement',
                'verbose_name_plural': 'evenementen',
                'abstract': False,
                'managed': True,
            },
            bases=('agenda.event',),
        ),
    ]
