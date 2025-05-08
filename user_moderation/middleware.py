from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import UserModeration, ModerationType

class UserModerationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Define paths that banned/suspended users can access
            allowed_paths = [
                reverse('account_logout'),
                '/accounts/logout/',  # Include allauth's logout path
                '/static/',
                '/media/'
            ]
            
            # Check for active ban
            active_ban = UserModeration.objects.filter(
                user=request.user,
                type=ModerationType.BAN,
                is_active=True
            ).first()
            
            if active_ban:
                current_path = request.path
                # Allow banned users to access logout
                if current_path == reverse('moderation_banned') or any(current_path.startswith(path) for path in allowed_paths):
                    # Let the request proceed
                    pass
                else:
                    return redirect('moderation_banned')
            
            # Check for active suspension
            active_suspension = UserModeration.objects.filter(
                user=request.user,
                type=ModerationType.SUSPENSION,
                is_active=True
            ).first()
            
            if active_suspension:
                # Check if suspension has expired
                if active_suspension.expires_at and timezone.now() > active_suspension.expires_at:
                    active_suspension.is_active = False
                    active_suspension.save()
                else:
                    # Define paths that suspended users can access
                    suspension_allowed_paths = [
                        reverse('home'),
                        reverse('profile_info'),
                        reverse('account_logout'),
                        reverse('inbox'),
                        reverse('moderation_suspended')
                    ] + allowed_paths
                    
                    # Check if current path or its parent path is in allowed_paths
                    current_path = request.path
                    path_allowed = any(current_path.startswith(path) for path in suspension_allowed_paths)
                    
                    # Block actions related to borrowing, requests, etc.
                    if not path_allowed:
                        messages.error(request, "Your account is currently suspended. You cannot perform this action.")
                        return redirect('moderation_suspended')
        
        response = self.get_response(request)
        return response