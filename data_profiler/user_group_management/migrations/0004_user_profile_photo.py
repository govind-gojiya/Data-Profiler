# Generated by Django 4.2.11 on 2024-04-18 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_group_management', '0003_alter_member_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.FileField(default='profile_photos/default.jpg', upload_to='profile_photos/'),
        ),
    ]