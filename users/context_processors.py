from django.utils import timezone
from datetime import timedelta
from user_moderation.models import UserModeration, ModerationType, get_user_role

def user_moderation_status(request):
    context = {}
    
    if request.user.is_authenticated:
        # Get user role
        context['role'] = get_user_role(request.user)
        
        # Get user's active suspension
        user_suspension = UserModeration.objects.filter(
            user=request.user,
            type=ModerationType.SUSPENSION,
            is_active=True
        ).first()
        
        if user_suspension and user_suspension.expires_at and timezone.now() > user_suspension.expires_at:
            user_suspension.is_active = False
            user_suspension.save()
            user_suspension = None
        
        context['user_suspension'] = user_suspension
        
        # Handle warnings
        active_warning = UserModeration.objects.filter(
            user=request.user,
            type=ModerationType.WARNING,
            is_active=True
        ).first()
        
        # Only show warning if not dismissed in this session
        if active_warning:
            warning_dismissed = request.session.get(f'warning_{active_warning.id}_dismissed', False)
            if not warning_dismissed:
                context['active_warning'] = active_warning
    
    return context