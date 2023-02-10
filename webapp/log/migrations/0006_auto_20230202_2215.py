# Generated by Django 2.2.28 on 2023-02-02 21:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0005_auto_20160315_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventlog',
            name='operator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='operator_logs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='eventlog',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_logs', to=settings.AUTH_USER_MODEL),
        ),
    ]