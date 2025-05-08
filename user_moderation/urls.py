from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_moderation_list, name='user_moderation'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('suspended/', views.moderation_suspended, name='moderation_suspended'),
    path('banned/', views.moderation_banned, name='moderation_banned'),
    path('remove/<int:moderation_id>/', views.remove_moderation, name='remove_moderation'),
    path('warning/dismiss/<int:warning_id>/', views.dismiss_warning, name='dismiss_warning'),
]