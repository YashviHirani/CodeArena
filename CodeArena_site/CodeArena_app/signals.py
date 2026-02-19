from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # Use get_or_create to prevent errors if Google login 
        # partially created the user already
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Save profile only if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()