# Generated by Django 4.2.6 on 2024-02-20 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_userdata_place_of_birth'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='place_of_birth',
            field=models.CharField(max_length=70, null=True),
        ),
    ]
