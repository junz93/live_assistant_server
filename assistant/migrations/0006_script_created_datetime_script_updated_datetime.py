# Generated by Django 4.2.3 on 2023-08-05 10:06

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0005_script'),
    ]

    operations = [
        migrations.AddField(
            model_name='script',
            name='created_datetime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='script',
            name='updated_datetime',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
