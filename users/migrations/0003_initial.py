# Generated by Django 5.2 on 2025-06-01 11:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0002_delete_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MoodleUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("moodle_stu_id", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="SiteUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("display_name", models.CharField(blank=True, max_length=100)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserMoodleLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "moodle_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.moodleuser",
                    ),
                ),
                (
                    "site_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="users.siteuser"
                    ),
                ),
            ],
        ),
    ]
