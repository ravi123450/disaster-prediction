# Generated by Django 5.0.7 on 2024-07-26 11:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("userapp", "0002_user_status"),
    ]

    operations = [
        migrations.DeleteModel(
            name="User",
        ),
    ]
