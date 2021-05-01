# Generated by Django 3.1.7 on 2021-03-12 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_authenticateduser_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authenticateduser',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('apache helicopter', 'Apache Helicopter'), ('a10 warthog', 'A10-WartHog'), ('blue hair', 'Blue Hair'), ('punk', 'Punk'), ('uwu', 'uWu'), ('gecko', 'Gecko'), ('vegan', 'Vegan'), ('west virgin', 'West Virgin'), ('none', 'No gender'), ('middle', 'Middle Gender'), ('quarter', 'Quarter Gender'), ('gender2', 'Gender 2')], default=None, max_length=100, null=True),
        ),
    ]
