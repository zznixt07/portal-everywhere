# Generated by Django 3.1.7 on 2021-03-15 16:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_loginuser'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LoginUser',
        ),
    ]
