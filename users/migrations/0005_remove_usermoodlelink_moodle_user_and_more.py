# Generated by Django 5.2 on 2025-06-10 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_siteuser_last_download_time_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usermoodlelink",
            name="moodle_user",
        ),
        migrations.RemoveField(
            model_name="usermoodlelink",
            name="site_user",
        ),
        migrations.DeleteModel(
            name="MoodleUser",
        ),
        migrations.DeleteModel(
            name="UserMoodleLink",
        ),
    ]
