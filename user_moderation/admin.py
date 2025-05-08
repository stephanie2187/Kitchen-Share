from django.contrib import admin
from .models import UserModeration

@admin.register(UserModeration)
class UserModerationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'created_by', 'created_at', 'expires_at', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('user__username', 'reason')
    date_hierarchy = 'created_at'
