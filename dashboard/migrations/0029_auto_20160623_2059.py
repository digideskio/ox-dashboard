# -*- coding: utf-8 -*-
# Generated by Django 1.10a1 on 2016-06-23 20:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0028_auto_20160623_0135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excuse',
            name='response_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
