# Generated by Django 3.1.7 on 2021-03-15 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_authenticateduser_times_queried'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=32)),
                ('password', models.CharField(max_length=64)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
