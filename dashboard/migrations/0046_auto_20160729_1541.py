# -*- coding: utf-8 -*-
# Generated by Django 1.10a1 on 2016-07-29 15:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0045_position_ec'),
    ]

    operations = [
        migrations.AlterField(
            model_name='position',
            name='ec',
            field=models.BooleanField(default=False),
        ),
    ]
