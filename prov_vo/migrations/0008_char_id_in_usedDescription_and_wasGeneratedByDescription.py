# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-01-24 13:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prov_vo', '0007_entitydescription_datatype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useddescription',
            name='id',
            field=models.CharField(max_length=128, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='wasgeneratedbydescription',
            name='id',
            field=models.CharField(max_length=128, primary_key=True, serialize=False),
        ),
    ]
