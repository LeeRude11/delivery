# Generated by Django 2.2.2 on 2019-06-21 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_menuitem_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menuitem',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
