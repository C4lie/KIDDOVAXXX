# Generated by Django 4.2.4 on 2023-08-17 13:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('adminapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patienttbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('address', models.CharField(max_length=500, verbose_name='Address')),
                ('contactNo', models.IntegerField(blank=True, null=True, verbose_name='Contact')),
                ('password', models.CharField(max_length=255, verbose_name='Password')),
                ('areaId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adminapp.area', verbose_name='Area')),
                ('cityId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adminapp.city', verbose_name='City')),
            ],
        ),
    ]
