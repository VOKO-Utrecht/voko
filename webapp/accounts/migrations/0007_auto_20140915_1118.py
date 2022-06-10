# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetRequest',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('token', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': b'wachtwoordreset-aanvraag',
                'verbose_name_plural': b'wachtwoordreset-aanvragen',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name': b'adres', 'verbose_name_plural': b'adressen'},
        ),
        migrations.AlterModelOptions(
            name='emailconfirmation',
            options={'verbose_name': b'emailbevestiging', 'verbose_name_plural': b'emailbevestigingen'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': b'ledenprofiel', 'verbose_name_plural': b'ledenprofielen'},
        ),
        migrations.AlterModelOptions(
            name='vokouser',
            options={'verbose_name': b'lid', 'verbose_name_plural': b'leden'},
        ),
    ]
