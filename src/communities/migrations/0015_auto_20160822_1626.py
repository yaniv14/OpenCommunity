# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-22 13:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0014_auto_20160804_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='committee',
            name='straw_voting_enabled',
            field=models.BooleanField(default=True, verbose_name='Straw voting enabled'),
        ),
        migrations.AlterField(
            model_name='community',
            name='straw_voting_enabled',
            field=models.BooleanField(default=True, verbose_name='Straw voting enabled'),
        ),
    ]
