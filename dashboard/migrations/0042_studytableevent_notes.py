# -*- coding: utf-8 -*-
# Generated by Django 1.10a1 on 2016-07-19 15:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0041_auto_20160707_1856'),
    ]

    operations = [
        migrations.AddField(
            model_name='studytableevent',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
