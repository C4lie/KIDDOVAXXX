# Generated by Django 4.2.4 on 2023-11-02 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patientapp', '0004_alter_appointmenttbl_patientid'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmenttbl',
            name='childname',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Child Name'),
        ),
    ]
