from django.db import models
from django.contrib.auth.models import User

class SiteUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    total_downloads = models.IntegerField(default=0)  # 總下載次數
    total_download_size = models.BigIntegerField(default=0)  # 總下載大小（位元組）
    last_download_time = models.DateTimeField(null=True, blank=True)  # 最後下載時間

    def __str__(self):
        return self.display_name or self.user.username

    def get_total_download_size_mb(self):
        """返回總下載大小（MB）"""
        return round(self.total_download_size / (1024 * 1024), 2)

class MoodleUser(models.Model):
    moodle_stu_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.moodle_name

class UserMoodleLink(models.Model):
    site_user = models.ForeignKey(SiteUser, on_delete=models.CASCADE)
    moodle_user = models.ForeignKey(MoodleUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.site_user} <-> {self.moodle_user}"

