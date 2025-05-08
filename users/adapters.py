# users/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import Group
from .models import UserProfile

class NoSignupSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Only handle new accounts
        if not sociallogin.is_existing:
            user = sociallogin.user
            # Force assignment as Patron
            patron_group, _ = Group.objects.get_or_create(name="Patron")
            user.save()  # Save the user to ensure it exists
            user.groups.add(patron_group)
            
            # Optionally, update the user profile role if you have one
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = "Patron"
            profile.save()
