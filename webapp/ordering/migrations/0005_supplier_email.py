# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0004_auto_20140916_1229'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='email',
            field=models.EmailField(default='todo@todo.nl', max_length=75),
            preserve_default=False,
        ),
    ]
