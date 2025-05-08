from django.urls import path
from .views import *

urlpatterns = [
    path('inbox/', inbox, name='inbox'),
    path('sent/', sent_messages, name='sent_messages'),
    path('send/', send_message, name='send_message'),
    path('read/<int:message_id>/', read_message, name='read_message'),
    path('api/unread-count/', unread_message_count_api, name='unread_message_count_api'),
]