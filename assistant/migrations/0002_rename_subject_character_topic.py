# Generated by Django 4.2.3 on 2023-07-28 14:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assistant', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='character',
            old_name='subject',
            new_name='topic',
        ),
    ]
