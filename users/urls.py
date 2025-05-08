from django.urls import path
from . import views
from .views import assign_patron_role, assign_librarian_role, manage_roles, promote_user, demote_user

urlpatterns = [
    path("", views.login, name="login"),
    path("home/", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("logout", views.logout_view),
    path("patron_login/", assign_patron_role, name="patron_login"),
    path("librarian_login/", assign_librarian_role, name="librarian_login"),
    path('users/', views.profile_info, name='profile_info'),
    path('profile/upload/', views.upload_profile_photo, name='upload_profile_photo'),
    path("profile/send-identity-verification-email/", views.send_identity_verification_email, name="send_identity_verification_email"),
    path('verify/<uidb64>/<token>/', views.verify_identity, name='verify_identity'),
    path('manage-roles/', manage_roles, name='manage_roles'),
    path('promote/<int:user_id>/', promote_user, name='promote_user'),
    path('demote/<int:user_id>/', demote_user, name='demote_user'),
    path('rate/<int:patron_id>/', views.rate_patron, name='rate_patron'),
]