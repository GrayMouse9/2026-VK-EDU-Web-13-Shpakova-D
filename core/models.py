import uuid
from pathlib import Path

from django.db import models
from django.contrib.auth.models import User

def avatar_upload_to(instance, filename):
    """
    Раскидывает аватарки по 2-уровневым подкаталогам,
    чтобы путь нельзя было перебрать.
    Пример: avatars/ab/cd/abcd1234-....jpg
    """
    ext = Path(filename).suffix.lower()
    name = uuid.uuid4().hex
    return f'avatars/{name[:2]}/{name[2:4]}/{name}{ext}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True, verbose_name='Аватар')

    def __str__(self):
        return f'Профиль {self.user.username}'

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
