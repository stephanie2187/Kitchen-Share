# Generated by Django 4.2.20 on 2025-04-15 15:32

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0004_patronrating'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='patronrating',
            unique_together={('librarian', 'patron')},
        ),
    ]
