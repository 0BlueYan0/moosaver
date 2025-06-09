from django.db import models
from django.contrib.auth.models import User

class SiteUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.display_name or self.user.username

class MoodleUser(models.Model):
    moodle_stu_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.moodle_name

class UserMoodleLink(models.Model):
    site_user = models.ForeignKey(SiteUser, on_delete=models.CASCADE)
    moodle_user = models.ForeignKey(MoodleUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.site_user} <-> {self.moodle_user}"

