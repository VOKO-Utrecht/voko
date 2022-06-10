# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0033_auto_20150503_1449'),
    ]

    operations = [
        migrations.CreateModel(
            name='DraftProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('data', jsonfield.fields.JSONField()),
                ('order_round', models.ForeignKey(to='ordering.OrderRound', on_delete=models.CASCADE)),
                ('supplier', models.ForeignKey(to='ordering.Supplier', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='productcategory',
            options={'verbose_name': 'Productcategorie', 'verbose_name_plural': 'Productcategorie\xebn'},
        ),
    ]
