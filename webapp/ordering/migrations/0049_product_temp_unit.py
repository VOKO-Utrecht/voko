# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0048_auto_20151018_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='temp_unit',
            field=models.ForeignKey(to='ordering.ProductUnit', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
