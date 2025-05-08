from django import forms
from django.contrib.auth.models import User
from .models import ModerationType, is_librarian

class ModerationForm(forms.Form):
    type = forms.ChoiceField(choices=ModerationType.choices, label="Moderation Action")
    reason = forms.CharField(widget=forms.Textarea, label="Reason")
    duration_days = forms.IntegerField(
        required=False, 
        min_value=1, 
        max_value=365,
        label="Duration (days, for suspension only)",
        help_text="Leave empty for warnings or permanent bans"
    )
    
    def __init__(self, *args, **kwargs):
        self.moderator = kwargs.pop('moderator', None)
        self.user_to_moderate = kwargs.pop('user_to_moderate', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        moderation_type = cleaned_data.get("type")
        duration_days = cleaned_data.get("duration_days")
        
        # Check if suspension requires duration
        if moderation_type == ModerationType.SUSPENSION and not duration_days:
            self.add_error('duration_days', "Duration is required for suspensions")
        
        # Role-based permission checks
        if self.moderator and self.user_to_moderate:
            # Librarians cannot moderate admins
            if is_librarian(self.moderator) and self.user_to_moderate.is_superuser:
                raise forms.ValidationError(
                    "As a librarian, you cannot moderate an administrator. "
                    "This action is not permitted."
                )
            
            # Librarians cannot moderate other librarians
            if (is_librarian(self.moderator) and is_librarian(self.user_to_moderate) 
                and not self.moderator.is_superuser):
                raise forms.ValidationError(
                    "As a librarian, you cannot moderate another librarian. "
                    "Only administrators can moderate librarians."
                )
            
            # Only superusers can ban or suspend librarians
            if (is_librarian(self.user_to_moderate) and not self.moderator.is_superuser
                and moderation_type in [ModerationType.BAN, ModerationType.SUSPENSION]):
                raise forms.ValidationError(
                    "Only administrators can suspend or ban librarians."
                )
                
        return cleaned_data


class UserSearchForm(forms.Form):
    search_query = forms.CharField(
        label="Search",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search by username or email'})
    )
    
    ROLE_CHOICES = (
        ('', 'All Roles'),
        ('librarian', 'Librarian'),
        ('patron', 'Patron'),
    )
    
    STATUS_CHOICES = (
        ('', 'All Statuses'),
        ('active', 'Active'),
        ('warning', 'Warned'),
        ('suspension', 'Suspended'),
        ('ban', 'Banned'),
    )
    
    role_filter = forms.ChoiceField(
        label="Role", 
        choices=ROLE_CHOICES,
        required=False
    )
    
    status_filter = forms.ChoiceField(
        label="Status", 
        choices=STATUS_CHOICES,
        required=False
    )