from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from allauth.account.signals import user_signed_up
from .models import UserProfile
from django.db.models.signals import pre_delete, pre_save

@receiver(user_signed_up)
def assign_patron_role_on_signup(request, user, **kwargs):
    patron_group, _ = Group.objects.get_or_create(name="Patron")
    user.groups.add(patron_group)
    request.session["current_role"] = "Patron"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=instance)
    profile.save()


@receiver(pre_delete, sender=UserProfile)
def delete_profile_picture(sender, instance, **kwargs):
    if instance.profile_picture:
        instance.profile_picture.delete(False)





@receiver(pre_save, sender=UserProfile)
def auto_delete_old_profile_picture(sender, instance, **kwargs):
    if not instance.pk:
        return  # new instance, nothing to delete
    try:
        old_file = UserProfile.objects.get(pk=instance.pk).profile_picture
    except UserProfile.DoesNotExist:
        return
    new_file = instance.profile_picture
    if old_file and old_file != new_file:
        old_file.delete(False)
