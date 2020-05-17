from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=15, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='pic', default='pic/default.png', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    class Meta:
        db_table = 'user_profile_userprofile'

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('profile:profile', kwargs={'username': self.user.username})


@receiver(post_save, sender=User)
def create_profile(sender, instance, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=instance)
