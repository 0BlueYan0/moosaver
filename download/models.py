from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DownloadRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_records')
    file_path = models.CharField(max_length=1024)
    size = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} downloaded {self.file_path} at {self.timestamp}'
