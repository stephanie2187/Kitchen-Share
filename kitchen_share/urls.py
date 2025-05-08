"""
URL configuration for kitchen_share project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from allauth.socialaccount.providers.google.views import oauth2_login, oauth2_callback
from allauth.account.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/google/login/', oauth2_login, name='google_login'),
    path('accounts/google/login/callback/', oauth2_callback, name='google_callback'),
    path('accounts/logout/', LogoutView.as_view(extra_context={'next_page': '/'}), name='account_logout'),

    path('accounts/login/', lambda request: redirect('/login/')),

    path("", include("users.urls")),

    path("accounts/", include("allauth.urls")),

    path("form/", include("form.urls")),
    
    #adding path for messaging
    path('messaging/', include('messaging.urls')),
  
    #adding path for adding items
    path('inventory/', include('inventory.urls')),

    #adding path for user moderation
    path('moderation/', include('user_moderation.urls')),

    path("accounts/", include("allauth.socialaccount.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)