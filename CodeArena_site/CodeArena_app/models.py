from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # 'upload_to' creates a subfolder inside /media/
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(default='default.png', upload_to='profile_pics')

    def __cl__(self):
        return f'{self.user.username} Profile'