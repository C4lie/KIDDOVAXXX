# Generated by Django 4.2.4 on 2023-09-04 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Adminreg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contactno', models.IntegerField(max_length=10, verbose_name='ContactNo')),
                ('password', models.CharField(max_length=200, verbose_name='Passwords')),
            ],
        ),
    ]
