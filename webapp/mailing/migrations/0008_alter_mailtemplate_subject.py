# Generated by Django 3.2.20 on 2023-08-11 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailing', '0007_alter_mailtemplate_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailtemplate',
            name='subject',
            field=models.CharField(default='VOKO Amersfoort - ', max_length=100),
        ),
    ]
