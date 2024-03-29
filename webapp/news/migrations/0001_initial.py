# Generated by Django 3.2.20 on 2023-12-02 20:30

from django.db import migrations, models
import django_extensions.db.fields
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Newsitem',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150, verbose_name='titel')),
                ('publish', models.BooleanField(default=False, verbose_name='publiceer')),
                ('publish_date', models.DateField(blank=True, null=True, verbose_name='publicatiedatum')),
                ('summary', models.CharField(blank=True, max_length=300, null=True, verbose_name='samenvatting')),
                ('content', tinymce.models.HTMLField(blank=True, null=True, verbose_name='bericht')),
            ],
            options={
                'verbose_name': 'nieuwsbericht',
                'verbose_name_plural': 'nieuwsberichten',
                'abstract': False,
                'managed': True,
            },
        ),
    ]
