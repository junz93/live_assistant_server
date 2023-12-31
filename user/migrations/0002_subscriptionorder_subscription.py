# Generated by Django 4.2.3 on 2023-08-18 16:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionOrder',
            fields=[
                ('order_id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('product_id', models.CharField(choices=[('SP1', '包年'), ('SP2', '包季'), ('SP3', '包月')], max_length=8)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('amount_str', models.CharField(max_length=15)),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('paid_datetime', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expiry_datetime', models.DateTimeField()),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('updated_datetime', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
