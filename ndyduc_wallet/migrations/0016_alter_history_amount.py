# Generated by Django 5.0.4 on 2024-05-18 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ndyduc_wallet', '0015_alter_history_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='history',
            name='amount',
            field=models.DecimalField(decimal_places=6, max_digits=10),
        ),
    ]
