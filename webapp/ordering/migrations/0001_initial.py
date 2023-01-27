# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20140915_0934'),
        ('finance', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('finalized', models.BooleanField(default=False)),
                ('collected', models.BooleanField(default=False)),
                ('debit', models.OneToOneField(null=True, blank=True, to='finance.Balance', on_delete=models.CASCADE)),
                ('payment', models.OneToOneField(null=True, blank=True, to='finance.Payment', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('amount', models.IntegerField(verbose_name=b'Aantal')),
                ('order', models.ForeignKey(to='ordering.Order', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderProductCorrection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('supplied_amount', models.DecimalField(max_digits=6, decimal_places=1)),
                ('notes', models.TextField(blank=True)),
                ('credit', models.OneToOneField(to='finance.Balance', on_delete=models.CASCADE)),
                ('order_product', models.OneToOneField(to='ordering.OrderProduct', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderRound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('open_for_orders', models.DateField()),
                ('closed_for_orders', models.DateField()),
                ('collect_date', models.DateField()),
                ('markup_percentage', models.DecimalField(default=7.0, max_digits=5, decimal_places=2)),
                ('transaction_costs', models.DecimalField(default=0.35, max_digits=5, decimal_places=2)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='order',
            name='order_round',
            field=models.ForeignKey(to='ordering.OrderRound', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('unit_of_measurement', models.CharField(max_length=2, choices=[(b'St', b'Stuk'), (b'G', b'Gram'), (b'KG', b'Kilogram'), (b'P', b'Pond'), (b'L', b'Liter')])),
                ('base_price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('minimum_total_order', models.IntegerField(null=True, blank=True)),
                ('order_round', models.ForeignKey(to='ordering.OrderRound', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='product',
            field=models.ForeignKey(to='ordering.Product', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(to='ordering.Product', through='ordering.OrderProduct'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('address', models.ForeignKey(to='accounts.Address', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(to='ordering.Supplier', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='SupplierOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('order_round', models.ForeignKey(to='ordering.OrderRound', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupplierOrderProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('amount', models.IntegerField()),
            ],
            options={
                'ordering': (b'-modified', b'-created'),
                'abstract': False,
                'get_latest_by': b'modified',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='supplierorder',
            name='products',
            field=models.ManyToManyField(to='ordering.Product', through='ordering.SupplierOrderProduct'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='supplierorderproduct',
            name='order',
            field=models.ForeignKey(to='ordering.SupplierOrder', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='supplierorderproduct',
            name='product',
            field=models.ForeignKey(to='ordering.Product', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
