from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=128)  # 儲存哈希後的密碼

    def save(self, *args, **kwargs):
        # 確保密碼被哈希儲存
        if self._state.adding or (
            'password' in self.__dict__ and 
            not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2'))
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    

    def __str__(self):
        return self.username
