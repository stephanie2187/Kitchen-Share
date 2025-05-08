from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

class ModerationType(models.TextChoices):
    WARNING = 'warning', 'Warning'
    SUSPENSION = 'suspension', 'Suspension'
    BAN = 'ban', 'Ban'

class UserModeration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderations')
    type = models.CharField(max_length=20, choices=ModerationType.choices)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='moderations_given')
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderations_removed')
    removal_reason = models.TextField(blank=True)
    
    @property
    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    @property
    def is_warning(self):
        return self.type == ModerationType.WARNING
    
    def remove(self, removed_by, reason=""):
        self.is_active = False
        self.removed_at = timezone.now()
        self.removed_by = removed_by
        self.removal_reason = reason
        self.save()
    
    def __str__(self):
        return f"{self.get_type_display()} for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Moderation Action"
        verbose_name_plural = "User Moderation Actions"

# Helper functions for user roles
def is_librarian(user):
    return user.groups.filter(name="Librarian").exists()

def is_patron(user):
    return user.groups.filter(name="Patron").exists()

def get_user_role(user):
    if user.is_superuser:
        return "Admin"
    elif is_librarian(user):
        return "Librarian"
    elif is_patron(user):
        return "Patron"
    else:
        return "Unknown"
