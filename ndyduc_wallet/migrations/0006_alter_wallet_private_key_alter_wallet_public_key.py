# Generated by Django 5.0.4 on 2024-05-06 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ndyduc_wallet', '0005_remove_result_kraken_remove_tokens_result_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet',
            name='private_key',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='public_key',
            field=models.CharField(max_length=1000),
        ),
    ]