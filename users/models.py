from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        SiteUser.objects.create(user=instance)

class MoodleAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moodle_accounts')
    student_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'student_id')

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

